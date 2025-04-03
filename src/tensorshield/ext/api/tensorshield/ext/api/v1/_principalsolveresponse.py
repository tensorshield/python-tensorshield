from typing import Union

from canonical.ext.jose import JWSCompactEncoded
from canonical.ext.jose import SignedJWS

from tensorshield.ext.api import RootResponseModel
from tensorshield.ext.api.models import OpenAuthorizationChallengeMethod
from tensorshield.ext.api.models import VerificationCodeChallengeMethod


ChallengeMethodType = Union[
    OpenAuthorizationChallengeMethod,
    VerificationCodeChallengeMethod
]


class PrincipalSolveResponse(RootResponseModel[JWSCompactEncoded | SignedJWS]):
    pass