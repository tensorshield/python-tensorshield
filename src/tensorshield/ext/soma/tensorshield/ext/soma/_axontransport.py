import asyncio
import threading
import os
from typing import Any
from typing import TypeVar
from typing import Union
from typing import TYPE_CHECKING

import fastapi
import uvicorn

from tensorshield.ext.protocol import Synapse
from tensorshield.ext.protocol import SynapseEnvelope
if TYPE_CHECKING:
    from ._soma import Soma


U = TypeVar('U')


class AxonTransport(threading.Thread):
    """Arranges communication between the :class:`~Soma` and the :class:`Axon`."""
    app: fastapi.FastAPI
    synapse_classes: tuple[type[Synapse], ...]

    @staticmethod
    def union(classes: Any):
        return Union[tuple(classes)]

    def __init__(
        self,
        soma: 'Soma[Any]',
        synapse_classes: list[type[Synapse]],
        host: str = '127.0.0.1',
        port: int = 8090
    ):
        super().__init__(
            daemon=True,
            target=self.main
        )
        self.soma = soma
        self.app = fastapi.FastAPI()
        self.host = host
        self.port = port
        self.running = threading.Event()
        self.synapse_classes = tuple(synapse_classes)
        self.config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level='critical',
            access_log=False,
        )
        self.server = uvicorn.Server(config=self.config)

    def is_running(self):
        return self.running.is_set()

    def main(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        SynapseType = self.union(self.synapse_classes)

        async def handle(
            envelope: SynapseEnvelope[SynapseType] # type: ignore
        ) -> fastapi.Response:
            return await self.submit(envelope) # type: ignore

        self.app.add_api_route(
            endpoint=handle, # type: ignore
            path='/v1/synapses',
            methods=['POST']
        )

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