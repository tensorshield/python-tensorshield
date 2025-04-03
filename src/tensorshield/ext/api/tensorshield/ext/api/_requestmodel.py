from typing import Any
from typing import ClassVar
from typing import Generic
from typing import TypeVar

import pydantic

from ._responsemodel import ResponseModel
from ._rootresponsemodel import RootResponseModel


R = TypeVar('R', bound=ResponseModel | RootResponseModel[Any])


class RequestModel(pydantic.BaseModel, Generic[R]):
    method: ClassVar[str] = 'POST'
    path: ClassVar[str]
    version: ClassVar[str]
    response_model: ClassVar[type[R]] # type: ignore

    @classmethod
    def urlpattern(cls):
        assert not str.startswith(cls.path, '/')
        return f'/{cls.version}/{cls.path}'

    def qualpath(self):
        assert not str.startswith(self.path, '/')
        return f'/{self.version}/{self.path}'