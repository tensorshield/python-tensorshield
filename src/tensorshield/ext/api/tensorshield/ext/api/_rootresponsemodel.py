from typing import Generic
from typing import TypeVar

import pydantic


T = TypeVar('T')


class RootResponseModel(pydantic.RootModel[T], Generic[T]):
    pass