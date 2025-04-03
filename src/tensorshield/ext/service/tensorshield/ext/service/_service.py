import contextlib
from typing import Self

import fastapi
from tensorshield.ext.subtensor import AsyncSubtensor


class Service(fastapi.FastAPI):
    chain_endpoint: str | None = None
    subtensor: AsyncSubtensor | None = None

    def __init__(
        self,
        chain_endpoint: str | None = None
    ):
        super().__init__(
            lifespan=self.default_lifespan
        )
        self.chain_endpoint = chain_endpoint

    @contextlib.asynccontextmanager
    async def default_lifespan(self, _: Self):
        if self.chain_endpoint:
            self.subtensor = AsyncSubtensor(chain_endpoint=self.chain_endpoint)
            await self.subtensor.connect()
        yield
        if self.subtensor is not None:
            await self.subtensor.close()