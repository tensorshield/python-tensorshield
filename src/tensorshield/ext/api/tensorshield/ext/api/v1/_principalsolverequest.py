import pydantic

from tensorshield.ext.api.models import MessageCodeChallengeAnswer
from ._annotations import PrincipalField
from ._requestmodel import V1RequestModel
from ._principalsolveresponse import PrincipalSolveResponse


class PrinicpalSolveRequest(V1RequestModel[PrincipalSolveResponse]):
    path = 'solve'

    principal: PrincipalField

    answer: MessageCodeChallengeAnswer = pydantic.Field(
        default=...,
        title="Answer",
        description=(
            "An artifact presented by the caller to prove its ownership of "
            "the specified `principal.`"
        )
    )