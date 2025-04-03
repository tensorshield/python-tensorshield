from typing import Generic
from typing import TypeVar

import pydantic


T = TypeVar('T')


class PrincipalChallengeMethod(pydantic.BaseModel, Generic[T]):
    name: T = pydantic.Field(
        default=...,
        title="Name",
        description="A string identifier for this specific verification method."
    )

    display_name: str = pydantic.Field(
        default=...,
        title="Display name",
        description=(
            "A human-readable name identifying the verification method."
        )
    )

    description: str = pydantic.Field(
        default=...,
        title="Description",
        description=(
            "A short description providing instructions to the end-user "
            "on how to perform this specific verification."
        )
    )