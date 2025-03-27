import logging
from typing import Any
from typing import Callable
from typing import Coroutine
from typing import Generic
from typing import TypeVar

import fastapi
import fastapi.routing
import starlette
import starlette.requests

from tensorshield.ext.protocol import Synapse
from ._request import SynapseRequest


S = TypeVar('S', bound=Synapse)


class SynapseRouteHandler(fastapi.routing.APIRoute, Generic[S]):
    logger: logging.Logger = logging.getLogger(__name__)
    synapse_class: type[S]

    @classmethod
    def build(
        cls,
        synapse_class: type[Any]
    ) -> type['SynapseRouteHandler[Any]']:
        return type(f'{synapse_class.__name__}', (cls, ), {
            'synapse_class': synapse_class
        })

    def get_route_handler(self) -> Callable[[starlette.requests.Request], Coroutine[Any, Any, fastapi.Response]]:
        handler = super().get_route_handler()

        async def f(request: starlette.requests.Request) -> fastapi.Response:
            request = SynapseRequest(
                model=self.synapse_class,
                scope=request.scope,
                receive=request.receive
            )
            return await handler(request)
        return f