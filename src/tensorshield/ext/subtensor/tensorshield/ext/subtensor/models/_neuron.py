import logging
from typing import ClassVar
from typing import TypeVar

import pydantic
from libcanonical.bases import StateLogger

from ._neuroninfo import NeuronInfo

S = TypeVar('S', bound='Neuron')


class Neuron(pydantic.BaseModel, StateLogger):
    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)
    active: bool = False
    coldkey: str
    consensus: float = 0.0
    dividends: float = 0.0
    emission: float = 0.0
    host: str = '0.0.0.0'
    hotkey: str
    incentive: float = 0.0
    port: int = 0
    rank: float = 0.0
    stake: float = 0.0
    total_stake: float = 0.0
    trust: float = 0.0
    uid: int = -1
    updated: int = 0

    validator_permit: bool = pydantic.Field(
        default=False
    )

    vrust: float = pydantic.Field(
        default=0.0
    )

    @classmethod
    def model_validate_neuroninfo(cls, neuroninfo: NeuronInfo):
        return cls.model_validate({
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
            'port': None if not neuroninfo.axon_info else neuroninfo.axon_info.port
        })

    def is_miner(self) -> bool:
        raise NotImplementedError

    def is_validator(self) -> bool:
        return bool(self.validator_permit) and self.vtrust > 0.0

    def is_registered(self):
        return self.uid >= 0

    def diff(self, neuron: 'Neuron') -> set[str]:
        changed: set[str] = set()
        for attname in self.model_fields.keys():
            if getattr(self, attname) == getattr(neuron, attname):
                continue
            changed.add(attname)
        return changed

    def update(self, neuron: 'Neuron') -> tuple['Neuron', 'Neuron', tuple[str, ...]]:
        adapter: pydantic.TypeAdapter[Neuron] = pydantic.TypeAdapter(Neuron)
        changed = self.diff(neuron)
        old = adapter.validate_python(self.model_dump())
        for k in changed:
            new = getattr(neuron, k)
            setattr(self, k, new)
        return old, neuron, tuple(changed)

    def __hash__(self) -> int:
        return hash(self.hotkey)