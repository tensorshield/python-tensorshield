import asyncio
from typing import Generic
from typing import TypeVar


E = TypeVar('E')
R = TypeVar('R')


class BaseSoma(Generic[E, R]):
    """Specifies the base interface to a :class:`~Soma`
    implementation.
    """

    async def discover(self) -> None:
        raise NotImplementedError

    def submit(
        self,
        envelope: E,
        *,
        loop: asyncio.AbstractEventLoop
    ) -> asyncio.Future[R]:
        raise NotImplementedError