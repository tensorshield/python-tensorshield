from typing import Generic
from typing import TypeVar

import pydantic
from libcanonical.types import DomainName
from libcanonical.types import HTTPResourceLocator


T = TypeVar('T')


class PrincipalChallengeMethod(pydantic.BaseModel, Generic[T]):
    name: T = pydantic.Field(
        default=...,
        title="Name",
        description="A string identifier for this specific verification method."
    )

    audience: DomainName = pydantic.Field(
        default=...,
        title="Audience",
        description=(
            "The `audience` parameter is a domain name that indicates the "
            "verification audience. Receivers of a `PrincipalAssertion` use "
            "this to determine if they want to accept the assertion."
        )
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

    scope: set[HTTPResourceLocator | str] = pydantic.Field(
        default=...,
        title="Scope",
        description=(
            "The `scope` parameter is an array of strings that may be used "
            "to constrain how the assertion is used."
        )
    )