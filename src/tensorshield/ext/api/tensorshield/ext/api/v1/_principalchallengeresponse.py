import pydantic

from tensorshield.ext.api import RootResponseModel


class PrincipalVerificationCodeChallengeResponse(pydantic.BaseModel):
    challenge_id: str = pydantic.Field(
        default=...,
        title="Challenge ID",
        description=(
            "An identifier for the created challenge. The caller must present "
            "this identifier alongside with its answer."
        )
    )

    max_attempts: int = pydantic.Field(
        default=...,
        title="Maximum attempts",
        description=(
            "The maximum number of failed attempts while solving the challenge before "
            "it expires."
        )
    )


class PrincipalChallengeResponse(RootResponseModel[PrincipalVerificationCodeChallengeResponse]):
    pass