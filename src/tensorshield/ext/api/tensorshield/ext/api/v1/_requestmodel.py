from typing import Any
from typing import TypeVar

from tensorshield.ext.api import RequestModel
from tensorshield.ext.api import ResponseModel
from tensorshield.ext.api import RootResponseModel


R = TypeVar('R', bound=ResponseModel | RootResponseModel[Any])


class V1RequestModel(RequestModel[R]):
    version = 'v1'