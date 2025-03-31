import asyncio
from typing import Generic
from typing import TypeVar

from tensorshield.ext.protocol import Synapse
from tensorshield.ext.protocol import SynapseEnvelope

E = TypeVar('E', bound=Synapse)
R = TypeVar('R')


class BaseSoma(Generic[E, R]):
    """Specifies the base interface to a :class:`~Soma`
    implementation.
    """

    async def discover(self) -> None:
        raise NotImplementedError

    def submit(
        self,
        envelope: SynapseEnvelope[E],
        *,
        loop: asyncio.AbstractEventLoop
    ) -> asyncio.Future[R]:
        raise NotImplementedError