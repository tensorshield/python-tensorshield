from typing import Union

import pydantic

from libcanonical.types import DomainName
from libcanonical.types import HTTPResourceLocator
from libcanonical.types import EmailAddress
from libcanonical.types import Phonenumber
from libtensorshield.types import SS58Address


PrincipalTypes = Union[
    DomainName,
    EmailAddress,
    Phonenumber,
    SS58Address
]


class PrincipalVerificationRequest(pydantic.BaseModel):
    """A :class:`PrincipalVerificationRequest` is a request by a
    client to verify a certain principal, such as an email address,
    phone number or username.
    """
    audience: DomainName = pydantic.Field(
        default=...,
        title="Audience",
        description=(
            "The `audience` parameter is a domain name that indicates the "
            "verification audience. Receivers of a `PrincipalAssertion` use "
            "this to determine if they want to accept the assertion."
        )
    )

    scope: set[HTTPResourceLocator | str] = pydantic.Field(
        default=...,
        title="Scope",
        description=(
            "The `scope` parameter is an array of strings that may be used "
            "to contrain how the assertion is used."
        )
    )

    principal: PrincipalTypes = pydantic.Field(
        default=...,
        title="Principal",
        description=(
            "The principal that the client requests to verify."
        )
    )