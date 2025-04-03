from typing import Union

import pydantic
from libcanonical.types import DomainName
from libcanonical.types import HTTPResourceLocator
from libcanonical.types import EmailAddress
from libcanonical.types import Phonenumber
from libtensorshield.types import SS58Address

from ._requestmodel import V1RequestModel
from ._principalverificationresponse import PrincipalVerificationResponse


PrincipalTypes = Union[
    DomainName,
    EmailAddress,
    Phonenumber,
    SS58Address
]


class PrincipalVerificationRequest(V1RequestModel[PrincipalVerificationResponse]):
    """A :class:`PrincipalVerificationRequest` is a request by a
    client to verify a certain principal, such as an email address,
    phone number or username.
    """
    path = 'request'
    response_model = PrincipalVerificationResponse
    version = 'v1'

    audience: DomainName = pydantic.Field(
        default=...,
        title="Audience",
        description=(
            "The `audience` parameter is a domain name that indicates the "
            "verification audience. Receivers of a `PrincipalAssertion` use "
            "this to determine if they want to accept the assertion."
        )
    )

    token: str | None = pydantic.Field(
        default=None,
        title="Security token",
        description=(
            "For audiences that do not allow anonymous verification requests, "
            "a security token that resolves to a `PreparedPrincipalVerification"
            "Request`."
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

    principal: PrincipalTypes = pydantic.Field(
        default=...,
        title="Principal",
        description=(
            "The principal that the client requests to verify."
        )
    )