from typing import Awaitable
from typing import Callable
from typing import Iterable

from libcanonical.runtime import MainProcess
from libcanonical.utils.logging import LoggingConfigDict

from ._metagraphobserver import MetagraphObserver
from ._metagraphthread import MetagraphThread


ObserverTypeOrFactory = Callable[
    ['MetagraphUplink', 'MetagraphThread'],
    MetagraphObserver | Awaitable[MetagraphObserver]
] | type[MetagraphObserver]


class MetagraphUplink(MainProcess):
    interval = 1
    workers: list[MetagraphThread]

    def __init__(
        self,
        *,
        name: str,
        lite_endpoint: str,
        archive_endpoint: str,
        subnets: Iterable[int],
        replay_max_blocks: int = 14400,
        replay_batch_size: int = 64,
        block: int = 0,
        observers: list[ObserverTypeOrFactory] | None = None
    ):
        super().__init__(name=name)
        self.archive_endpoint = archive_endpoint
        self.block = block
        self.lite_endpoint = lite_endpoint
        self.replay_batch_size = replay_batch_size
        self.replay_max_blocks = replay_max_blocks
        self.observers = observers or []
        self.subnets = subnets
        self.workers = []

    def get_logging_config(self) -> LoggingConfigDict:
        config = super().get_logging_config()
        config['loggers']['tensorshield'] = config['loggers']['canonical']
        return config

    async def start_subnet(self, netuid: int):
        m = MetagraphThread(
            uplink=self,
            netuid=netuid,
            block=self.block,
            chain_endpoint=self.lite_endpoint,
            archive_endpoint=self.archive_endpoint,
            replay_batch_size=self.replay_batch_size,
            replay_max_blocks=self.replay_max_blocks
        )
        for observer in self.observers:
            m.observe(observer)
        m.start()
        return m

    async def configure(self, reloading: bool = False) -> None:
        if not reloading:
            for netuid in self.subnets:
                self.workers.append(await self.start_subnet(netuid))
        else:
            for i, worker in enumerate(self.workers):
                worker.stop()
                self.workers[i] = await self.start_subnet(worker.netuid)

    async def main_event(self) -> None:
        for i, netuid in enumerate(self.subnets):
            if self.workers[i].is_alive():
                continue
            self.logger.warning(
                "Worker thread for subnet %s died, restarting.",
                netuid
            )
            self.workers[i] = await self.start_subnet(netuid)