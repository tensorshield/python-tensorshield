from typing import Literal

import pydantic
from libcanonical.types import HTTPResourceLocator

from ._principalchallengemethod import PrincipalChallengeMethod


NameType = Literal['oauth2']


class OpenAuthorizationChallengeMethod(PrincipalChallengeMethod[NameType]):
    redirect_uri: HTTPResourceLocator = pydantic.Field(
        default=...,
        title="Redirect URI",
        description=(
            "An URI to that the end-user must visit to solve the challenge."
        )
    )