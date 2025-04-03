from typing import Literal

import pydantic
from libcanonical.types import EmailAddress
from libcanonical.types import Phonenumber

from ._principalchallengeoption import PrincipalChallengeMethod


NameType = Literal['code']


class VerificationCodeChallengeMethod(PrincipalChallengeMethod[NameType]):
    receiver: EmailAddress | Phonenumber = pydantic.Field(
        default=...,
        title="Receiver",
        description=(
            "Specifies the receiver of the verification code."
        )
    )