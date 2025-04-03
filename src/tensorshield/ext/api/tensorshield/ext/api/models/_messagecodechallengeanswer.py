import pydantic


class MessageCodeChallengeAnswer(pydantic.BaseModel):
    code: str = pydantic.Field(
        default=...,
        max_length=8,
        title="Code",
        description="The secret code sent to the specified principal."
    )