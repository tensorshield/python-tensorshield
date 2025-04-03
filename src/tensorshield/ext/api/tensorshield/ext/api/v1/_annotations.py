from typing import Annotated
from typing import Union

import pydantic
from libcanonical.types import DomainName
from libcanonical.types import EmailAddress
from libcanonical.types import HTTPResourceLocator
from libcanonical.types import Phonenumber
from libtensorshield.types import SS58Address

from tensorshield.ext.api.models import OpenAuthorizationChallengeMethod
from tensorshield.ext.api.models import VerificationCodeChallengeMethod


__all__: list[str] = [
    'ChallengeMethodType',
    'PrincipalType'
]


ChallengeMethodType = Union[
    OpenAuthorizationChallengeMethod,
    VerificationCodeChallengeMethod
]

PrincipalType = Union[
    DomainName,
    EmailAddress,
    Phonenumber,
    SS58Address
]

PrincipalAudienceField = Annotated[
    DomainName,
    pydantic.Field(
        default=...,
        title="Audience",
        description=(
            "The `audience` parameter is a domain name that indicates the "
            "verification audience. Receivers of a `PrincipalAssertion` use "
            "this to determine if they want to accept the assertion."
        ),
        examples=['tensorshield.ai']
    )
]

PrincipalField = Annotated[
    PrincipalType,
    pydantic.Field(
        default=...,
        title="Principal",
        description=(
            "The principal that the client requests to verify."
        )
    )
]

PrincipalScopeField = Annotated[
    set[HTTPResourceLocator | str],
    pydantic.Field(
        default=...,
        title="Scope",
        max_length=64,
        description=(
            "The `scope` parameter is an array of strings that may be used "
            "to constrain how a principal assertion is used."
        )
    )
]