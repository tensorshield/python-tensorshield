import asyncio
import threading
import os
from typing import cast
from typing import Any
from typing import Iterable
from typing import Literal

import fastapi
from libcanonical.bases import StateLogger
from uvicorn import Server
from uvicorn import Config

from tensorshield.ext.bases import BaseSoma
from tensorshield.ext.protocol import Synapse
from tensorshield.ext.subtensor import MetagraphThread
from tensorshield.ext.wallet import Hotkey
from tensorshield.ext.wallet import HotkeySet
from tensorshield.ext.protocol import SynapseEnvelope
from ._apiroute import SynapseRouteHandler
from ._request import SynapseRequest
from ._router import SynapseRouter


AuthorizationFailureReason = Literal[
    'SIGNATURE_INVALID',
    'UNREGISTERED_NEURON',
    'INSUFFICIENT_STAKE',
    'NO_VALIDATOR_PERMIT',
]



class Axon(threading.Thread, StateLogger):
    __module__: str = 'tensorshield.ext.axon'
    allow_unregistered: bool = False
    force_validator_permit: bool = True
    min_stake: float = 4096.0
    soma: BaseSoma[Any, fastapi.Response]

    def __init__(
        self,
        soma: BaseSoma[Any, fastapi.Response],
        metagraph: 'MetagraphThread',
        hotkeys: list[Hotkey],
        host: str,
        port: int,
        synapse_types: Iterable[type[Synapse]] | None = None,
        allow_unregistered: bool = False,
        force_validator_permit: bool = True,
        min_stake: float = 4096.0,
    ):
        super().__init__(
            daemon=True,
            target=self.main_event_loop
        )
        self.app = fastapi.FastAPI()
        self.allow_unregistered = allow_unregistered
        self.force_validator_permit  = force_validator_permit
        self.host = host
        self.port = port
        self.metagraph = metagraph
        self.hotkeys = HotkeySet(items={h.ss58_address: h for h in hotkeys})
        self.min_stake = min_stake
        self.running = threading.Event()
        self.soma = soma
        self.synapse_types = list(synapse_types or [])
        for synapse_class in self.synapse_types:
            self.attach(synapse_class)

    async def authorize(self, request: fastapi.Request, fatal: bool = True) -> bool:
        request = cast(SynapseRequest[Any], request)
        conditions: list[AuthorizationFailureReason] = []

        # Verify the signature first.
        if not request.verify():
            conditions.append('SIGNATURE_INVALID')

        validator = self.metagraph.neuron(
            request.validator_hotkey,
            validator_permit=self.force_validator_permit
        )
        if not validator.is_registered() and not self.allow_unregistered:
            conditions.append('UNREGISTERED_NEURON')

        if (validator.stake < self.min_stake) and not self.allow_unregistered:
            # Unregistered neurons are assumed to never have stake in a
            # subnet.
            conditions.append('INSUFFICIENT_STAKE')

        if self.force_validator_permit and not validator.validator_permit:
            conditions.append('NO_VALIDATOR_PERMIT')

        for condition in conditions:
            match condition:
                case 'SIGNATURE_INVALID':
                    request.log(
                        'CRITICAL', "Signature did not validate (hotkey: %s)",
                        request.validator_hotkey
                    )
                case 'UNREGISTERED_NEURON':
                    request.log(
                        'CRITICAL', "Signer is not registered as a validator (hotkey: %s)",
                        request.validator_hotkey
                    )
                case 'INSUFFICIENT_STAKE':
                    request.log(
                        'CRITICAL', "Validator does not have sufficient stake (uid: %s)",
                        validator.uid
                    )
                case 'NO_VALIDATOR_PERMIT':
                    request.log(
                        'CRITICAL', "Validator does not have a validator permit (uid: %s)",
                        validator.uid
                    )

        if bool(conditions) and fatal:
            raise fastapi.HTTPException(
                status_code=403
            )

        return not bool(conditions)

    def attach(self, synapse_class: type[Synapse]):
        """Exposes an endpoint to handle a synapse of the given class."""
        self.logger.info(
            "Accepting %s at http://%s:%s/%s",
            synapse_class.__name__,
            self.host,
            self.port,
            synapse_class.__name__
        )
        router: SynapseRouter[Any] = SynapseRouter(
            route_class=SynapseRouteHandler.build(synapse_class)
        )
        router.add_api_route(
            path=f'/{synapse_class.__name__}',
            endpoint=self.default_handler,
            methods=['POST'],
            response_model=synapse_class,
            response_description=(
                "The provided synapse updated with the results from the "
                "neuron."
            )
        )
        self.app.include_router(
            router=router,
            include_in_schema=True,
            dependencies=[
                fastapi.Depends(self.authorize)
            ]
        )

    async def default_handler(self, request: fastapi.Request) -> fastapi.Response:
        return await self.submit(await cast(SynapseRequest[Any], request).envelope())

    def is_running(self):
        return self.running.is_set()

    def main_event_loop(self):
        self.config = Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level='critical',
            access_log=False,
        )
        self.server = Server(config=self.config)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        for synapse_class in self.synapse_types:
            self.attach(synapse_class)
        try:
            self.running.set()
            self.loop.run_until_complete(
                self.server.serve(sockets=[self.config.bind_socket()])
            )
        finally:
            self.running.clear()
            if self.config.uds and os.path.exists(self.config.uds):
                os.remove(self.config.uds)  # pragma: py-win32

    def stop(self):
        self.server.should_exit = True
        self.join()

    def submit(
        self,
        envelope: SynapseEnvelope[Any]
    ) -> asyncio.Future[fastapi.Response]:
        return self.soma.submit(envelope, loop=self.loop)

    def wait(self):
        return self.running.wait()