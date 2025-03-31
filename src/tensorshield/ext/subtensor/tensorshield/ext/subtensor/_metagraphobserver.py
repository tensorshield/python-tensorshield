import contextlib
import logging
from typing import Awaitable
from typing import TYPE_CHECKING

from libtensorshield.types import Neuron
if TYPE_CHECKING:
    from ._metagraphthread import MetagraphThread
    from ._metagraphuplink import MetagraphUplink


class MetagraphObserver:
    logger: logging.Logger = logging.getLogger(__name__)

    @property
    def netuid(self):
        return self.metagraph.netuid

    def __init__(
        self,
        uplink: 'MetagraphUplink',
        metagraph: 'MetagraphThread'
    ):
        self.uplink = uplink
        self.metagraph = metagraph
        self.initialize()

    def initialize(self):
        pass

    @contextlib.asynccontextmanager
    async def block(self, block: int):
        await self.begin(block)
        try:
            yield self
            await self.commit(block)
        except:
            await self.rollback(block)
            raise

    async def setup(self):
        pass

    async def on_configured(self, metagraph: 'MetagraphThread'):
        """This method is invoked just prior to entering the main event
        loop. Override this for additional thread-bound configuration.
        """
        pass

    async def begin(self, block: int) -> None:
        raise NotImplementedError

    async def commit(self, block: int) -> None:
        raise NotImplementedError

    async def rollback(self, block: int):
        pass

    async def teardown(self):
        pass

    def on_neurons_updated(
        self,
        current: int,
        block: int,
        active: list[Neuron],
        changed: set[tuple[Neuron, Neuron, tuple[str, ...]]],
        joined: set[Neuron],
        dropped: set[Neuron],
        replay: bool = False
    ) -> None | Awaitable[None]:
        pass

    def on_neuron_changed(
        self,
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
        netuid: int,
        current: int,
        block: int,
        neuron: Neuron,
        replay: bool = False
    ) -> None | Awaitable[None]:
        pass

    def on_neuron_joined(
        self,
        netuid: int,
        current: int,
        block: int,
        neuron: Neuron,
        immunity_length: int | None,
        replay: bool = False
    ) -> None | Awaitable[None]:
        pass