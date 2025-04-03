import pydantic

from ._annotations import ChallengeMethodType
from ._annotations import PrincipalAudienceField
from ._annotations import PrincipalScopeField
from ._annotations import PrincipalType
from ._requestmodel import V1RequestModel
from ._principalchallengeresponse import PrincipalChallengeResponse



class PrincipalChallengeRequest(V1RequestModel[PrincipalChallengeResponse]):
    path = 'challenge'
    response_model = PrincipalChallengeResponse
    version = 'v1'

    audience: PrincipalAudienceField

    scope: PrincipalScopeField

    using: ChallengeMethodType = pydantic.Field(
        default=...,
        title="Verification method",
        description=(
            "Describes the method that the caller wants to use to "
            "verify the principal."
        )
    )

    principal: PrincipalType = pydantic.Field(
        default=...,
        title="Principal",
        description=(
            "The principal that the client requests to verify."
        )
    )