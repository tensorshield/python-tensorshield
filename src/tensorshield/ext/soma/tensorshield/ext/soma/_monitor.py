import asyncio
import logging
import threading
import os
from typing import Any
from typing import TypeVar
from typing import TYPE_CHECKING

import fastapi
import uvicorn

if TYPE_CHECKING:
    from ._soma import Soma


U = TypeVar('U')


class Monitor(threading.Thread):
    app: fastapi.FastAPI

    def __init__(
        self,
        soma: 'Soma[Any]',
        host: str = '127.0.0.1',
        port: int = 8888,
    ):
        super().__init__(
            daemon=True,
            target=self.main_event_loop
        )
        self.app = fastapi.FastAPI()
        self.host = host
        self.soma = soma
        self.port = port

    async def live(self):
        status_code = 503
        if self.soma.is_live():
            status_code = 200
        return fastapi.Response(status_code=status_code)

    async def ready(self):
        status_code = 503
        if self.soma.is_ready():
            status_code = 200
        return fastapi.Response(status_code=status_code)

    async def startup(self):
        """Indicates a succesful startup of the application."""
        return fastapi.Response(status_code=200)

    def main_event_loop(self):
        self.loop = asyncio.new_event_loop()
        self.logger = logging.getLogger('tensorshield')
        self.config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level='critical',
            access_log=False,
        )
        self.server = uvicorn.Server(config=self.config)

        self.logger.info(
            "Exposing liveness endpoint at http://%s:%s/live",
            self.host, self.port
        )
        self.app.add_api_route(
            endpoint=self.live,
            path='/live',
            include_in_schema=False,
            methods=['GET']
        )

        self.logger.info(
            "Exposing readyness endpoint at http://%s:%s/ready",
            self.host, self.port
        )
        self.app.add_api_route(
            endpoint=self.ready,
            path='/ready',
            include_in_schema=False,
            methods=['GET']
        )

        self.logger.info(
            "Exposing startup endpoint at http://%s:%s/startup",
            self.host, self.port
        )
        self.app.add_api_route(
            endpoint=self.startup,
            path='/startup',
            include_in_schema=False,
            methods=['GET']
        )

        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(
                self.server.serve(sockets=[self.config.bind_socket()])
            )
        finally:
            if self.config.uds and os.path.exists(self.config.uds):
                os.remove(self.config.uds)  # pragma: py-win32

    def stop(self):
        self.server.should_exit = True
        self.join()