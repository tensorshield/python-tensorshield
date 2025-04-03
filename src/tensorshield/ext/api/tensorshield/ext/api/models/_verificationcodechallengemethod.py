from typing import Literal

from ._principalchallengemethod import PrincipalChallengeMethod


NameType = Literal['code']


class VerificationCodeChallengeMethod(PrincipalChallengeMethod[NameType]):
    """Verifies the ownership of a principal, such as an email address or
    phone number, using a one-time verification code.
    """
    pass