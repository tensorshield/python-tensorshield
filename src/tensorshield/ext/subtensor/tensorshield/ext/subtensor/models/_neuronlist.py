# Copyright (C) 2022-2025 Cochise Ruhulessin
#
# All rights reserved. No warranty, explicit or implicit, provided. In
# no event shall the author(s) be liable for any claim or damages.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
from typing import Any
from typing import TYPE_CHECKING

import pydantic

from ._neuron import Neuron
if TYPE_CHECKING:
    from tensorshield.ext.subtensor import AsyncSubtensor


NeuronType = Neuron


class NeuronList(pydantic.BaseModel):
    block: int = pydantic.Field(
        default=0
    )

    netuid: int = pydantic.Field(
        default=...
    )

    items: list[Neuron] = pydantic.Field(
        default_factory=list
    )

    _index: dict[str, Neuron] = pydantic.PrivateAttr(
        default_factory=dict
    )

    def get(self, hotkey: str) -> Neuron | None:
        return self._index.get(str(hotkey))

    def model_post_init(self, _: Any):
        self._index = {str(x.hotkey): x for x in self.items}

    async def update(
        self,
        subtensor: 'AsyncSubtensor',
        netuid: int,
        block: int | None = None
    ):
        self.block = block or await subtensor.get_current_block()
        adapter: pydantic.TypeAdapter[NeuronType] = pydantic.TypeAdapter(NeuronType)
        current: list[Neuron] = []
        joined: set[NeuronType] = set()
        changed: set[tuple[NeuronType, NeuronType, tuple[str, ...]]] = set()

        for neuroninfo in await subtensor.neurons(netuid=netuid, block=block):
            current.append(
                adapter.validate_python({
                    'hotkey': neuroninfo.hotkey,
                    'coldkey': neuroninfo.coldkey,
                    'uid': neuroninfo.uid,
                    'active': neuroninfo.active,
                    'stake': float(neuroninfo.stake),
                    'total_stake': float(neuroninfo.total_stake),
                    'rank': neuroninfo.rank,
                    'emission': neuroninfo.emission,
                    'inventive': neuroninfo.incentive,
                    'concensur': neuroninfo.consensus,
                    'trust': neuroninfo.trust,
                    'vtrust': neuroninfo.validator_trust,
                    'dividends': neuroninfo.dividends,
                    'last_update': neuroninfo.last_update,
                    'validator_permit': neuroninfo.validator_permit,
                    'host': None if not neuroninfo.axon_info else neuroninfo.axon_info.ip,
                    'port': None if not neuroninfo.axon_info else neuroninfo.axon_info.port,
                })
            )

        joined = {x for x in current if x.hotkey not in self._index} # type: ignore
        index: dict[str, NeuronType] = {x.hotkey: x for x in joined}
        for new in current:
            if new in joined:
                continue
            diff = self._index[new.hotkey].update(new)
            if diff:
                changed.add(diff)
            index[new.hotkey] = self._index[new.hotkey]

        # All neurons that are not in the new index are dropped.
        dropped: set[NeuronType] = {
            n for n in self._index.values() # type: ignore
            if n.hotkey not in index
        }

        self._index = index
        self.items = list(sorted(self._index.values(), key=lambda x: x.rank))
        return changed, joined, dropped