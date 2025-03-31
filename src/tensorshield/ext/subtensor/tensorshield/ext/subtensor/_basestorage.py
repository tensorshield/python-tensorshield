import functools
from typing import TypeVar

from libtensorshield.types import Neuron


T = TypeVar('T')


class BaseMetagraphStorage:
    netuid: int

    async def begin(self, netuid: int, block: int) -> None:
        raise NotImplementedError

    async def create_schema(self) -> None:
        pass

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError

    async def count(self, netuid: int) -> int:
        """Return the number of neurons registered on the network."""
        raise NotImplementedError

    async def dispose(self) -> None:
        raise NotImplementedError

    async def latest(self, netuid: int) -> int:
        """Return the latest block number that was fully processed."""
        raise NotImplementedError

    async def persist_many(
        self,
        instances: list[Neuron]
    ) -> None:
        raise NotImplementedError

    @functools.singledispatchmethod
    async def persist(self, instance: T, force_insert: bool = False) -> T:
        raise NotImplementedError