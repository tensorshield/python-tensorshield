import contextlib
from typing import Awaitable
from typing import TYPE_CHECKING

from .models import Neuron
if TYPE_CHECKING:
    from ._metagraphthread import MetagraphThread


class MetagraphObserver:

    @contextlib.asynccontextmanager
    async def block(self, block: int):
        await self.begin(block)
        try:
            yield self
            await self.commit(block)
        except:
            await self.rollback(block)

    async def begin(self, block: int) -> None:
        raise NotImplementedError

    async def commit(self, block: int) -> None:
        raise NotImplementedError

    async def rollback(self, block: int):
        pass

    def on_neurons_updated(
        self,
        current: int,
        block: int,
        changed: set[tuple[Neuron, Neuron, tuple[str, ...]]],
        joined: set[Neuron],
        dropped: set[Neuron],
        replay: bool = False
    ) -> None | Awaitable[None]:
        pass

    def on_neuron_changed(
        self,
        metagraph: 'MetagraphThread',
        netuid: int,
        current: int,
        block: int,
        old: Neuron,
        new: Neuron,
        diff: tuple[str, ...],
        replay: bool = False
    ) -> None | Awaitable[None]:
        pass

    def on_neuron_dropped(
        self,
        metagraph: 'MetagraphThread',
        netuid: int,
        current: int,
        block: int,
        neuron: Neuron,
        replay: bool = False
    ) -> None | Awaitable[None]:
        pass

    def on_neuron_joined(
        self,
        metagraph: 'MetagraphThread',
        netuid: int,
        current: int,
        block: int,
        neuron: Neuron,
        immunity_length: int | None,
        replay: bool = False
    ) -> None | Awaitable[None]:
        pass