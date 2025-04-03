from typing import Literal

from ._principalchallengemethod import PrincipalChallengeMethod


NameType = Literal['oauth2']


class OpenAuthorizationChallengeMethod(PrincipalChallengeMethod[NameType]):
    """Verifies the ownership of a principal using the OAuth 2.0 protocol."""