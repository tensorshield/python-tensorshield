import pydantic

from ._annotations import PrincipalAudienceField
from ._annotations import PrincipalScopeField
from ._annotations import PrincipalType
from ._requestmodel import V1RequestModel
from ._principalverificationresponse import PrincipalVerificationResponse


class PrincipalVerificationRequest(V1RequestModel[PrincipalVerificationResponse]):
    """A :class:`PrincipalVerificationRequest` is a request by a
    client to verify a certain principal, such as an email address,
    phone number or username.
    """
    path = 'discover'
    response_model = PrincipalVerificationResponse
    version = 'v1'

    audience: PrincipalAudienceField

    scope: PrincipalScopeField

    token: str | None = pydantic.Field(
        default=None,
        title="Security token",
        description=(
            "For audiences that do not allow anonymous verification requests, "
            "a security token that resolves to a `PreparedPrincipalVerification"
            "Request`."
        )
    )

    principal: PrincipalType = pydantic.Field(
        default=...,
        title="Principal",
        description=(
            "The principal that the client requests to verify."
        )
    )