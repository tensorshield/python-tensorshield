from typing import Generic
from typing import TypeVar

import fastapi

from tensorshield.ext.protocol import Synapse
from ._apiroute import SynapseRouteHandler


S = TypeVar('S', bound=Synapse)


class SynapseRouter(fastapi.APIRouter, Generic[S]):
    """A :class:`fastapi.APIRouter` implementation that provided additional
    interfaces to register synapse routes.
    """
    __module__: str = 'tensorshield.ext.axon.routing'
    route_class: type[SynapseRouteHandler[S]]