from typing import Generic
from typing import TypeVar

from tensorshield.ext.protocol import Synapse
from tensorshield.ext.soma import Soma


S = TypeVar('S', bound=Synapse)


class Miner(Soma[S], Generic[S]):
    pass