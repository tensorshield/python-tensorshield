import logging
from typing import Any
from typing import ClassVar

import pydantic

from ._neuron import Neuron
from ._neuroninfo import NeuronInfo


NeuronType = Neuron


class NeuronList(pydantic.BaseModel):
    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)
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

    def update(
        self,
        netuid: int,
        block: int,
        neurons: list[NeuronInfo]
    ):
        adapter: pydantic.TypeAdapter[NeuronType] = pydantic.TypeAdapter(NeuronType)
        current: list[Neuron] = []
        joined: set[NeuronType] = set()
        changed: set[tuple[NeuronType, NeuronType, tuple[str, ...]]] = set()

        for neuroninfo in neurons:
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
                    'consensus': neuroninfo.consensus,
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
            if diff[-1]:
                changed.add(diff)
                self.logger.debug(
                    "Neuron %s/%s changed fields: %s",
                    netuid,
                    new.uid,
                    str.join(', ', diff[-1])
                )
            index[new.hotkey] = self._index[new.hotkey]

        # All neurons that are not in the new index are dropped.
        dropped: set[NeuronType] = {
            n for n in self._index.values() # type: ignore
            if n.hotkey not in index
        }

        # Prevent marking neurons as joined when instantiating an empty
        # NeuronList.
        if not self.items:
            joined = set()

        self._index = index
        self.items = list(sorted(self._index.values(), key=lambda x: x.rank))
        return changed, joined, dropped