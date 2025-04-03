from typing import TypeVar

from tensorshield.ext.api import RequestModel
from tensorshield.ext.api import ResponseModel


R = TypeVar('R', bound=ResponseModel)


class V1RequestModel(RequestModel[R]):
    version = 'v1'