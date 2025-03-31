import contextlib
import functools
from typing import TypeVar

from libtensorshield.types import Neuron
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession

from tensorshield.ext.subtensor import BaseMetagraphStorage
from ._base import Base
from ._metagraphblock import MetagraphBlock
from ._neuronregistration import NeuronRegistration
from ._registeredneurons import RegisteredNeuron


__all__: list[str] = [
    'metadata',
    'Base',
    'BaseMetagraphStorage',
    'MetagraphBlock',
    'NeuronRegistration'
]

metadata = Base.metadata

T = TypeVar('T')


class SQLMetagraphStorage(BaseMetagraphStorage):
    engine: AsyncEngine
    netuid: int
    session: AsyncSession | None = None

    def __init__(self):
        # TODO: This assumes that SQLMetagraphStorage is not shared
        # between event loops. 
        self.engine = create_async_engine('sqlite+aiosqlite:///database.db')
        self.session_factory = async_sessionmaker(bind=self.engine)

    async def begin(self, netuid: int, block: int):
        self.netuid = netuid
        self.session = self.session_factory()
        await self.session.begin()
        self.session.add(MetagraphBlock(netuid=netuid, block=block))
        await self.session.flush()

    async def commit(self):
        assert self.session is not None
        await self.session.commit()

    async def create_schema(self) -> None:
        async with self.engine.begin() as tx:
            try:
                await tx.run_sync(metadata.create_all)
            except OperationalError:
                # Assume that the tables are created.
                pass

    async def rollback(self):
        assert self.session is not None
        await self.session.rollback()

    async def count(self, netuid: int):
        q = select(func.count(RegisteredNeuron.uid)).where(RegisteredNeuron.netuid==netuid)
        async with self.cursor() as c:
            return (await c.execute(q)).scalar() or 0

    async def latest(self, netuid: int) -> int:
        q = select(func.max(MetagraphBlock.block)).where(MetagraphBlock.netuid==netuid)
        async with self.cursor() as c:
            return (await c.execute(q)).scalar() or 0

    @functools.singledispatchmethod
    async def persist(self, instance: T, force_insert: bool = False) -> T:
        raise NotImplementedError(type(instance).__name__)

    async def persist_many(self, instances: list[Neuron]) -> None:
        assert self.session is not None
        self.session.add_all([RegisteredNeuron(netuid=self.netuid, **x.model_dump()) for x in instances])

    @persist.register
    async def _(self, instance: Neuron, force_insert: bool = False):
        assert self.session is not None
        dao = RegisteredNeuron(**instance.model_dump())
        if force_insert: self.session.add(dao)
        else: await self.session.merge(dao)

    @contextlib.asynccontextmanager
    async def cursor(
        self,
        cursor: AsyncConnection | None = None
    ):
        if cursor is not None:
            yield cursor
            return
        async with self.engine.connect() as cursor:
            yield cursor