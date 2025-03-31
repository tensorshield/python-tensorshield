import asyncio
import inspect
import ipaddress
import os
import pathlib
from typing import Any
from typing import AsyncGenerator
from typing import Awaitable
from typing import Callable
from typing import TypeAlias
from typing import TypeVar
from typing import ParamSpec
from typing import Union

import fastapi
from libcanonical.runtime import MainProcess
from libcanonical.types import ApplicationRuntimeState
from libcanonical.types import FatalException
from libcanonical.utils import deephash
from libcanonical.utils.logging import LoggingConfigDict

from tensorshield.ext.axon import Axon
from tensorshield.ext.axon import SynapseResponse
from tensorshield.ext.bases import BaseSoma
from tensorshield.ext.protocol import Synapse
from tensorshield.ext.protocol import SynapseEnvelope
from tensorshield.ext.settings import get_chain_endpoint
from tensorshield.ext.settings import Environment as BittensorEnvironment
from tensorshield.ext.settings import DEFAULT_NETWORK
from tensorshield.ext.subtensor import MetagraphThread
from tensorshield.ext.wallet import Hotkey
from ._axontransport import AxonTransport
from ._monitor import Monitor
from ._taskrunner import TaskRunner


F = TypeVar('F')
P = ParamSpec('P')
S = TypeVar('S', bound=Synapse)

Self = TypeVar('Self', bound='Soma[Any]')

SynapseHandlerType: TypeAlias = Union[
    Callable[..., AsyncGenerator[None | Exception | SynapseResponse, Synapse | None]],
    Callable[..., Awaitable[None | SynapseResponse]]
]

SynapseTask: TypeAlias = AsyncGenerator[None | SynapseResponse, Synapse | None]


class Soma(MainProcess, BaseSoma[S, fastapi.Response]):
    """The base class for all neuron implementations."""
    axon_class: type[Axon] = Axon
    config_class: type[BittensorEnvironment] = BittensorEnvironment
    futures: set[asyncio.Future[Any]]
    interval = 0.25
    monitor_class: type[Monitor] = Monitor
    synapse_classes: list[type[Synapse]]
    synapse_handlers: dict[str, SynapseHandlerType]
    tasks: TaskRunner
    task_identifier_exclude: set[str] = {'axon', 'dendrite'}

    @staticmethod
    def get_chain_endpoint(network: str):
        return get_chain_endpoint(network)

    @classmethod
    def fromenv(cls, name: str, **kwargs: Any):
        env = cls.config_class.model_validate_env({
            **os.environ,
            **{k: v for k, v in kwargs.items() if v is not None}
        })
        if env.netuid is None:
            raise FatalException(
                "Unable to infer netuid from the environment. Set "
                "the BT_SUBNET_UID environment variable to specify "
                "the subnet."
            )
        return cls(
            name=name,
            network=env.network,
            netuid=env.netuid,
            axon_ip=env.axon_ip,
            axon_port=env.axon_port,
            chain_endpoint=env.chain_endpoint,
            disable_axon=env.axon_disabled,
            hotkeys=list(env.enabled_hotkeys)
        )

    @classmethod
    def register(cls, synapse_class: Any) -> Any:
        def decorator(func: Any):
            func.synapse_class = synapse_class
            return func

        return decorator

    def __init__(
        self,
        name: str,
        netuid: int,
        hotkeys: list[Hotkey] | None = None,
        network: str = DEFAULT_NETWORK,
        chain_endpoint: str | None = None,
        axon_ip: ipaddress.IPv4Address = ipaddress.IPv4Address('0.0.0.0'),
        axon_port: int = 8091,
        disable_axon: bool = False,
        wallet_path: pathlib.Path = pathlib.Path('~/.bittensor/wallets'),
        monitoring_bind: str = '0.0.0.0',
        monitoring_port: int = 8888
    ):
        super().__init__(name=name)
        self.axon_ip = axon_ip
        self.axon_port = axon_port
        self.disable_axon = disable_axon
        self.futures = set()
        self.hotkeys = hotkeys or []
        self.metagraph = MetagraphThread(
            uplink=self, # type: ignore
            netuid=netuid,
            chain_endpoint=chain_endpoint or self.get_chain_endpoint(network)
        )
        self.monitoring_bind = monitoring_bind
        self.monitoring_port = monitoring_port
        self.netuid = netuid
        self.network = network
        self.synapse_classes = []
        self.synapse_handlers = {}
        self.wallet_path = wallet_path.expanduser()

    def generate_task_id(self, synapse: S) -> str:
        """Generates a task identifier for an incoming synapse. Task identifiers
        are used to identify similar tasks so that the scheduler can optimize
        execution.
        """
        if not synapse.dendrite:
            raise TypeError("The synapse.dendrite attribute can not be None.")
        return deephash(
            (
                synapse.dendrite.hotkey,
                synapse.model_dump(exclude=self.task_identifier_exclude)
             ),
            encode='hex',
            using='sha256'
        )

    def get_logging_config(self) -> LoggingConfigDict:
        config = super().get_logging_config()
        config['loggers']['tensorshield'] = config['loggers']['canonical']
        return config

    def log_status(self):
        if not self.metagraph.wait(timeout=0.1):
            self.logger.critical("Metagraph is not up-to-date (age: %.02fs)", self.metagraph.age)
        self.logger.info(
            'Running on subnet %s (metagraph-age: %.02fs, step: %s, runtime: %.02f)',
            self.netuid,
            self.metagraph.age,
            self.step,
            self.runtime,
        )
        for hotkey in self.hotkeys:
            neuron = self.metagraph.neuron(hotkey.ss58_address)
            match neuron.is_registered():
                case True:
                    self.logger.info(
                        "Hotkey %s: UID %s (incentive: %s, trust: %s, emission: %s)",
                        neuron.hotkey,
                        neuron.uid,
                        neuron.incentive,
                        neuron.trust,
                        neuron.emission
                    )
                case False:
                    self.logger.info(
                        "Hotkey %s: unregistered (incentive: %s, trust: %s, emission: %s)",
                        neuron.hotkey,
                        neuron.incentive,
                        neuron.trust,
                        neuron.emission
                    )

    def must_report(self):
        return all([
            self.runtime > 1,
            self.interval >= 1.0,
            int(self.runtime) % 15 == 0
        ])

    def submit(
        self,
        envelope: SynapseEnvelope[S],
        *,
        loop: asyncio.AbstractEventLoop
    ) -> asyncio.Future[fastapi.Response]:
        future = loop.create_future()
        self.tasks.schedule(envelope, future)
        return future

    async def configure(self, reloading: bool = False):
        if not reloading:
            self.logger.info("Booting %s", self.name)
            self.monitor = self.monitor_class(
                soma=self,
                host=self.monitoring_bind,
                port=self.monitoring_port
            )
            self.monitor.start()
            await self.setstate(ApplicationRuntimeState.STARTUP)

            for key in self.hotkeys:
                key.load(self.wallet_path, mode='public')
                self.logger.info(
                    "Loaded hotkey %s/%s (ss58: %s)",
                    key.name,
                    key.hotkey,
                    key.ss58_address
                )

            # Ensure that all components have access to the
            # handlers.
            self._register_handlers()

            # Start the metagraph and ensure that the main event loop
            # starts with an up-to-date set of neurons.
            self.metagraph.start()
            self.logger.info(
                "Starting metagraph and awaiting initial update."
            )
            self.metagraph.wait()
            self.logger.info(
                "Commencing main event loop after successful metagraph update."
            )

            # Task runner needs to be available before the transport
            # starts.
            self.tasks = TaskRunner(
                soma=self,
                loop=self.loop,
                handlers=self.synapse_handlers
            )

            # Start transport to receive synapses. For now this is an
            # HTTP server, but other protocols might be considered.
            if self.disable_axon:
                self.transport = AxonTransport(
                    soma=self,
                    synapse_classes=self.synapse_classes
                )
            else:
                self.transport = self.axon_class(
                    soma=self, # type: ignore
                    metagraph=self.metagraph,
                    host=str(self.axon_ip),
                    port=self.axon_port,
                    hotkeys=self.hotkeys,
                    synapse_types=self.synapse_classes
                )
            self.transport.start()
            self.transport.wait()
            self.logger.info(
                "Bound axon transport to %s:%s",
                self.transport.host,
                self.transport.port
            )
            await self.setstate(ApplicationRuntimeState.LIVE)
            self.logger.info("%s succesfully bootstrapped.", type(self).__name__)

    def add_future(
        self,
        awaitable: asyncio.Future[Any] | Awaitable[Any]
    ):
        if not isinstance(awaitable, asyncio.Future):
            awaitable = asyncio.ensure_future(awaitable)
        self.futures.add(awaitable)

    async def main_event(self) -> None:
        if not self.transport.is_running():
            self.logger.critical("Transport exited unexpectedly.")
            self.stop()
            return
        if self.must_report():
            self.log_status()
        if self.futures:
            _, self.futures = await asyncio.wait(self.futures, timeout=0.05)
        self.add_future(self.tasks.run_all())

    async def teardown(self) -> None:
        self.transport.stop()
        if self.futures:
            _, running = await asyncio.wait(
                self.futures,
                timeout=self.teardown_deadline
            )
            if running:
                self.logger.critical(
                    "%s tasks did not complete within teardown deadline.",
                    len(running)
                )
                for future in running:
                    future.cancel()
        self.metagraph.stop()
        self.monitor.stop()

    async def run_axon(self) -> None:
        raise NotImplementedError

    def _register_handlers(self):
        for _, value in inspect.getmembers(self):
            if not hasattr(value, 'synapse_class'):
                continue
            cls: type[Synapse] = getattr(value, 'synapse_class')
            qualname = cls.__name__
            self.synapse_classes.append(cls)
            self.synapse_handlers[qualname] = value
            self.logger.info(
                "Initialized %s handler function.",
                qualname
            )