from typing import ClassVar
from typing import Generic
from typing import TypeVar

import pydantic

from ._responsemodel import ResponseModel


R = TypeVar('R', bound=ResponseModel)


class RequestModel(pydantic.BaseModel, Generic[R]):
    method: ClassVar[str] = 'POST'
    path: ClassVar[str]
    version: ClassVar[str]
    response_model: ClassVar[type[R]] # type: ignore

    def qualpath(self):
        assert not str.startswith(self.path, '/')
        return f'/{self.version}/{self.path}'