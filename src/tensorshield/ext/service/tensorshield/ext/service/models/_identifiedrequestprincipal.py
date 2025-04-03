from typing import Generic
from typing import TypeVar

import pydantic


T = TypeVar('T')


class IdentifiedRequestPrincipal(pydantic.BaseModel, Generic[T]):
    ident: T = pydantic.Field(
        default=...
    )

    verified: bool = pydantic.Field(
        default=False
    )