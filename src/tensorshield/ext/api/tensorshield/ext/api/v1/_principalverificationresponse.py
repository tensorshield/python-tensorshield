from typing import Union

import pydantic

from tensorshield.ext.api import ResponseModel
from tensorshield.ext.api.models import OpenAuthorizationChallengeMethod
from tensorshield.ext.api.models import VerificationCodeChallengeMethod


ChallengeMethodType = Union[
    OpenAuthorizationChallengeMethod,
    VerificationCodeChallengeMethod
]


class PrincipalVerificationResponse(ResponseModel):
    options: list[ChallengeMethodType] = pydantic.Field(
        default_factory=list,
        title="Verification options",
        description=(
            "An array of `VerificationCodeChallengeOption` objects that "
            "the caller may use to verify the principal."
        )
    )