import asyncio
import contextlib
import functools
import inspect
import logging
import socket
from typing import Any
from typing import Awaitable
from typing import TypeVar
from typing import TYPE_CHECKING

import pydantic
from libcanonical.bases import PollingExternalState
from libcanonical.utils import chunks
from libcanonical.utils import retry
from websockets.exceptions import InvalidStatus

from libtensorshield.types import Neuron
from libtensorshield.types import NeuronInfo
from libtensorshield.types import NeuronList
from ._asyncsubtensor import AsyncSubtensor
from ._metagraphobserver import MetagraphObserver
if TYPE_CHECKING:
    from ._metagraphuplink import MetagraphUplink
    from ._metagraphuplink import ObserverTypeOrFactory


DEFAULT_NETWORK: str = 'finney'

SubstrateFailure = type('SubstrateFailure', (Exception,), {})
F = TypeVar('F')

NETWORK_ERRORS: list[type[BaseException]] = [
    ConnectionError,
    TimeoutError,
    socket.gaierror,
    InvalidStatus,
    SubstrateFailure
]


class MetagraphThread(PollingExternalState):
    """Keeps a real-time state of the Bittensor metagraph on the network
    and subnet specified.
    """
    __module__: str = 'libtensorshield.ext.subtensor'
    block: int = 0
    logger_name = 'tensorshield'
    neurons: NeuronList
    observers: list[MetagraphObserver]
    observer_factories: list['ObserverTypeOrFactory']
    replay_max_blocks: int = 14400
    replay_batch_size: int = 128
    subtensor: AsyncSubtensor | None = None

    @staticmethod
    def catch_substrate_ws_failure(
        func: F
    ) -> F:
        @functools.wraps(func) # type: ignore
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs) # type: ignore
            except AttributeError as e:
                if e.name != 'ws': raise
                raise SubstrateFailure
        return wrapper # type: ignore

    def __init__(
        self,
        uplink: 'MetagraphUplink',
        chain_endpoint: str,
        netuid: int = 0,
        interval: float = 0.1,
        immediate: bool = False,
        block: int = 0,
        archive_endpoint: str | None = None,
        replay_max_blocks: int = replay_max_blocks,
        replay_batch_size: int = replay_batch_size
    ):
        super().__init__(interval=interval, immediate=immediate)
        self.archive_endpoint = archive_endpoint
        self.block = block
        self.chain_endpoint = chain_endpoint
        self.logger = logging.getLogger('tensorshield') # type: ignore
        self.netuid = netuid
        self.neurons = NeuronList(netuid=self.netuid, block=0)
        self.replay_batch_size = replay_batch_size
        self.replay_max_blocks = replay_max_blocks
        self.observers = []
        self.observer_factories = []
        self.uplink = uplink

    def get_subtensor(self) -> AsyncSubtensor:
        return AsyncSubtensor(chain_endpoint=self.chain_endpoint)

    def neuron(
        self,
        hotkey: str,
        validator_permit: bool | None = True
    ) -> Neuron:
        adapter: pydantic.TypeAdapter[Neuron] = pydantic.TypeAdapter(Neuron)
        neuron = self.neurons.get(str(hotkey))
        if neuron is None:
            neuron = adapter.validate_python({
                'coldkey': '',
                'hotkey': hotkey,
                'uid': -1,
                'validator_permit': validator_permit
            })
        return neuron

    def observe(
        self,
        observer: 'ObserverTypeOrFactory'
    ):
        if isinstance(observer, MetagraphObserver): self.observers.append(observer)
        else: self.observer_factories.append(observer)

    def setready(self):
        if len(self.neurons.items) > 0:
            super().setready()

    def stop(self):
        self.logger.info("Stopping metagraph.")
        self.must_stop = True
        self.join()

    @contextlib.asynccontextmanager
    async def archive(self, latest:int , block: int):
        if self.archive_endpoint is None:
            raise ValueError(
                f"{type(self).__name__}.archive_endpoint must not be None when "
                "instantiating a connection to the archived network."
            )
        async with AsyncSubtensor(chain_endpoint=self.archive_endpoint) as subtensor:
            yield subtensor

    @contextlib.asynccontextmanager
    async def begin(self, block: int):
        try:
            await asyncio.gather(*[o.begin(block) for o in self.observers])
            yield
            await self.commit(block)
            self.block = block
        except:
            await self.rollback(block)
            raise

    async def commit(self, block: int):
        await asyncio.gather(*[o.commit(block) for o in self.observers])

    async def rollback(self, block: int):
        await asyncio.gather(*[o.rollback(block) for o in self.observers])

    async def get_target_block(self, subtensor: AsyncSubtensor, current: int):
        # Compare the current block against the known state. If they are
        # equal, then there is nothing to do.
        latest_block = await subtensor.get_current_block()
        block = min(current + 1, latest_block)
        if latest_block == block:
            return block, latest_block, 0

        # Determine which block to synchronize.
        if (latest_block - block) > 2:
            self.logger.critical(
                "State is %s blocks behind (netuid: %s, block: %s)",
                latest_block - block,
                self.netuid,
                block,
            )
        return block, latest_block, latest_block - block

    @retry(NETWORK_ERRORS, reason='Bittensor network unreachable.')
    @catch_substrate_ws_failure
    async def main_event(self) -> None:
        self.subtensor = self.get_subtensor()
        async with self.subtensor:
            block, current, behind = await self.get_target_block(
                subtensor=self.subtensor,
                current=self.block
            )
            if block == self.block:
                self.logger.debug(
                    "Metagraph state is up-to-date (netuid: %s, block: %s)",
                    self.netuid,
                    block,
                )
                await asyncio.sleep(6)
                return

            if behind > 16 and self.archive_endpoint:
                await self.replay(block, current, behind)
                await asyncio.sleep(6)
                return

            # If we are starting, and there is no archive endpoint, assume that the
            # caller is not interested in the historical metagraph states.
            if self.step == 1 and not self.archive_endpoint:
                self.block = current - 1
                block = current

            try:
                await self.update(
                    current=self.block,
                    block=block,
                    neurons=await self.subtensor.neurons(netuid=self.netuid, block=block),
                    immunity_length=await self.subtensor.immunity_period(
                        netuid=self.netuid,
                        block=self.block
                    )
                )
            except Exception as e:
                self.logger.exception(
                    "Caught fatal %s: %s",
                    type(e).__name__,
                    repr(e)
            )

    @retry(NETWORK_ERRORS, reason='Bittensor network unreachable.')
    @catch_substrate_ws_failure
    async def replay(self, block: int, current: int, n: int):
        start_block = max(current - self.replay_max_blocks, current - n)
        self.logger.warning(
            "Replaying %s blocks starting %s (netuid: %s, current: %s)",
            min(n, current - start_block),
            start_block,
            self.netuid,
            current,
        )

        block_neurons: list[tuple[int, int | None, list[NeuronInfo]]]
        async with self.archive(current, start_block) as subtensor:
            for chunk in chunks(range(start_block, current, 1), n=self.replay_batch_size):
                block_neurons = (
                    await asyncio.gather(*[
                        self.get_neurons(subtensor, current, x)
                        for x in chunk
                    ]
                ))
                self.logger.debug(
                    "Retrieved %s blocks (netuid: %s, current: %s)",
                    len(block_neurons),
                    self.netuid,
                    current
                )
                for block, immunity_length, neurons in sorted(block_neurons, key=lambda x: x[0]):
                    await self.update(current, block, neurons, immunity_length, replay=True)
                if self.must_stop:
                    break


    @retry(NETWORK_ERRORS, reason='Bittensor network unreachable.')
    async def get_neurons(
        self,
        subtensor: AsyncSubtensor,
        current: int,
        block: int
    ) -> tuple[int, int | None, list[NeuronInfo]]:
        if self.must_stop:
            return block, None, []
        self.logger.debug(
            "Fetching neurons for block %s (netuid: %s, behind: %s)",
            block,
            self.netuid,
            current - block
        )
        return (
            block,
            await subtensor.immunity_period(netuid=self.netuid, block=block),
            await subtensor.neurons(netuid=self.netuid, block=block)
        )

    async def on_neurons_updated(
        self,
        current: int,
        block: int,
        active: list[Neuron],
        changed: set[tuple[Neuron, Neuron, tuple[str, ...]]],
        joined: set[Neuron],
        dropped: set[Neuron],
        immunity_length: int | None,
        replay: bool = False
    ) -> None:
        results: list[None | Awaitable[None]] = [
            o.on_neurons_updated(current, block, active, changed, joined, dropped, replay=replay)
            for o in self.observers
        ]
        futures = list(filter(lambda x: inspect.isawaitable(x), results))
        if futures:
            await asyncio.gather(*[
                asyncio.ensure_future(future) for future in futures
            ])
        futures = [
            *[
                self.on_neuron_changed(current, block, old, new, diff, replay=replay)
                for old, new, diff in changed
            ],
            *[
                self.on_neuron_dropped(current, block, neuron, replay=replay)
                for neuron in dropped
            ],
            *[
                self.on_neuron_joined(current, block, neuron, immunity_length, replay=replay)
                for neuron in dropped
            ],
        ]
        if futures:
            await asyncio.gather(*[asyncio.ensure_future(future) for future in futures])

    async def on_neuron_changed(
        self,
        current: int,
        block: int,
        old: Neuron,
        new: Neuron,
        diff: tuple[str, ...],
        replay: bool = False
    ) -> None:
        results: list[None | Awaitable[None]] = [
            o.on_neuron_changed(self.netuid, current, block, old, new, diff, replay=replay)
            for o in self.observers
        ]
        futures = list(filter(lambda x: inspect.isawaitable(x), results))
        if futures:
            await asyncio.gather(*[
                asyncio.ensure_future(future) for future in futures
            ])

    async def on_neuron_dropped(
        self,
        current: int,
        block: int,
        neuron: Neuron,
        replay: bool = False
    ) -> None:
        results: list[None | Awaitable[None]] = [
            o.on_neuron_dropped(self.netuid, current, block, neuron, replay=replay)
            for o in self.observers
        ]
        futures = list(filter(lambda x: inspect.isawaitable(x), results))
        if futures:
            await asyncio.gather(*[
                asyncio.ensure_future(future) for future in futures
            ])

    async def on_neuron_joined(
        self,
        current: int,
        block: int,
        neuron: Neuron,
        immunity_length: int | None,
        replay: bool = False
    ) -> None:
        results: list[None | Awaitable[None]] = [
            o.on_neuron_joined(self.netuid, current, block, neuron, immunity_length, replay=replay)
            for o in self.observers
        ]
        futures = list(filter(lambda x: inspect.isawaitable(x), results))
        if futures:
            await asyncio.gather(*[
                asyncio.ensure_future(future) for future in futures
            ])

    async def update(
        self,
        current: int,
        block: int,
        neurons: list[NeuronInfo],
        immunity_length: int | None,
        replay: bool = False
    ):
        assert (self.block == block - 1) or replay
        async with self.begin(block):
            if replay:
                self.logger.debug(
                    "Replaying block %s (netuid: %s, latest: %s, local: %s)",
                    block,
                    self.netuid,
                    current,
                    self.block
                )
            changed, joined, dropped = self.neurons.update(
                netuid=self.netuid,
                block=block,
                neurons=neurons
            )
            if any([changed, joined, dropped]):
                self.log(
                    'INFO', (
                        "Metagraph update block %s (netuid: %s, joined: %s, "
                        "changed: %s, dropped: %s, behind: %s)"
                    ),
                    self.block,
                    self.netuid,
                    len(joined),
                    len(changed),
                    len(dropped),
                    current - block
                )
            await self.on_neurons_updated(
                current=current,
                block=block,
                active=self.neurons.items,
                changed=changed,
                joined=joined,
                dropped=dropped,
                immunity_length=immunity_length,
                replay=replay
            )
        self.immunity_length = immunity_length

    async def setup(self, reloading: bool = False) -> None:
        if reloading:
            return
        for factory in self.observer_factories:
            observer = factory(self.uplink, self)
            if inspect.isawaitable(observer):
                observer = await observer
            if not isinstance(observer, MetagraphObserver):
                raise TypeError(
                    "Factory function did not produce a MetagraphObserver "
                    "instance."
                )
            self.observers.append(observer)

        if self.observers:
            await asyncio.gather(*[x.setup() for x in self.observers])

        if self.observers:
            await asyncio.gather(*[x.on_configured(self) for x in self.observers])

    async def teardown(self, exception: BaseException | None = None) -> bool:
        if self.observers:
            await asyncio.gather(*[x.teardown() for x in self.observers])
        return False