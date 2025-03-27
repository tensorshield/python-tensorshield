from typing import Generic
from typing import TypeVar

import pydantic

from ._synapse import Synapse
from ._synapseheader import SynapseHeader


S = TypeVar('S', bound=Synapse)


class SynapseEnvelope(pydantic.BaseModel, Generic[S]):
    remote_host: str
    remote_port: int | None = None
    headers: SynapseHeader
    synapse: S

    @classmethod
    def annotate(cls, synapse_class: type[S]) -> type['SynapseEnvelope[S]']:
        return SynapseEnvelope[synapse_class]