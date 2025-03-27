# Copyright (C) 2022-2025 Cochise Ruhulessin
#
# All rights reserved. No warranty, explicit or implicit, provided. In
# no event shall the author(s) be liable for any claim or damages.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
import socket

import pydantic
from libcanonical.bases import PollingExternalState
from libcanonical.utils import retry

from .models import Neuron
from .models import NeuronList
from ._asyncsubtensor import AsyncSubtensor


DEFAULT_NETWORK: str = 'finney'

NETWORK_ERRORS: list[type[BaseException]] = [
    ConnectionError,
    TimeoutError,
    socket.gaierror
]


class MetagraphThread(PollingExternalState):
    """Keeps a real-time state of the Bittensor metagraph on the network
    and subnet specified.
    """
    __module__: str = 'canonical.ext.bittensor'
    block: int = 0
    neurons: NeuronList
    subtensor: AsyncSubtensor | None = None

    def __init__(
        self,
        chain_endpoint: str,
        netuid: int = 0,
        interval: float = 10,
        immediate: bool = False,
    ):
        self.chain_endpoint = chain_endpoint
        self.netuid = netuid
        self.neurons = NeuronList(netuid=self.netuid, block=0)
        super().__init__(interval=interval, immediate=immediate)

    def get_subtensor(self) -> AsyncSubtensor:
        return AsyncSubtensor(chain_endpoint=self.chain_endpoint)

    def neuron(
        self,
        hotkey: str,
        validator_permit: bool | None = True
    ) -> Neuron:
        adapter: pydantic.TypeAdapter[Neuron] = pydantic.TypeAdapter(Neuron)
        neuron = self.neurons.get(str(hotkey))
        if neuron is None:
            neuron = adapter.validate_python({
                'coldkey': '',
                'hotkey': hotkey,
                'uid': -1,
                'validator_permit': validator_permit
            })
        return neuron

    def setready(self):
        if len(self.neurons.items) > 0:
            super().setready()

    def stop(self):
        self.logger.info("Stopping metagraph.")
        self.must_stop = True
        self.join()

    @retry(NETWORK_ERRORS, reason='Bittensor network unreachable.')
    async def main_event(self) -> None:
        assert self.subtensor is not None
        last_block = self.block
        self.block = await self.subtensor.get_current_block()
        if last_block == self.block:
            return
        try:
            changed, joined, dropped = await self.neurons.update(
                subtensor=self.subtensor,
                netuid=self.netuid,
                block=self.block
            )
            self.log(
                'INFO', "Metagraph update block %s (joined: %s, changed: %s, dropped: %s)",
                self.block,
                len(joined),
                len(changed),
                len(dropped)
            )
        except Exception as e:
            self.logger.exception(
                "Caught fatal %s: %s",
                type(e).__name__,
                repr(e)
            )

    @retry(NETWORK_ERRORS, reason='Bittensor network unreachable.')
    async def setup(self, reloading: bool = False) -> None:
        if reloading:
            if self.subtensor is not None:
                await self.subtensor.close()
        self.subtensor = self.get_subtensor()
        await self.subtensor.__aenter__()

    @retry(NETWORK_ERRORS, max_attempts=5, delay=1, reason='Bittensor network unreachable.')
    async def teardown(
        self,
        exception: BaseException | None = None
    ) -> bool:
        if self.subtensor is not None:
            await self.subtensor.close()
        return False