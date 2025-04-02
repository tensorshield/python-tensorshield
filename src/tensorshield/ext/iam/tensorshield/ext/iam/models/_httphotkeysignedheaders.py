import hashlib

import fastapi
import pydantic
from libcanonical.types import DomainName
from libcanonical.types import HTTPResourceLocator
from libtensorshield.types import SS58Address
from tensorshield.ext.wallet import Hotkey

from tensorshield.ext.iam.types import AuthorizationHeader


class HTTPHotkeySignedHeaders(pydantic.BaseModel):
    model_config = {'populate_by_name': True}

    authorization: AuthorizationHeader = pydantic.Field(
        default=...
    )

    audience: SS58Address | DomainName | HTTPResourceLocator | None = pydantic.Field(
        default=None,
        alias='X-Bittensor-Audience'
    )

    nonce: int = pydantic.Field(
        default=...,
        alias='X-Bittensor-Nonce'
    )

    hotkey: SS58Address = pydantic.Field(
        default=...,
        alias='X-Bittensor-Hotkey'
    )

    network: str | None = pydantic.Field(
        default=None,
        alias='X-Bittensor-Network'
    )

    netuid: int | None = pydantic.Field(
        default=None,
        alias='X-Bittensor-Subnet-ID'
    )

    @property
    def digest_algorithm(self) -> str:
        return self.authorization.digest_algorithm

    @property
    def signature(self) -> bytes:
        return bytes.fromhex(self.authorization.signature)

    @classmethod
    def model_validate_request(cls, request: fastapi.Request):
        try:
            self = cls.model_validate(request.headers)
        except pydantic.ValidationError: # pragma: no cover
            raise fastapi.HTTPException(
                status_code=403,
                detail="Authentication protocol violation."
            )
        return self

    def sign_response(self, signer: Hotkey,  body: bytes):
        h = hashlib.new(self.digest_algorithm)
        h.update(body)
        return bytes.hex(signer.sign(h.digest()))

    def verify(self, body: bytes | None = None):
        h = hashlib.new(self.digest_algorithm)
        headers: dict[str, str] = {
            str.lower(k): str(v)
            for k, v in self.model_dump(by_alias=True, exclude={'authorization'}).items()
            if v is not None
        }
        for k, v in sorted(headers.items(), key=lambda x: x[0]):
            h.update(str.encode(k, 'ascii'))
            h.update(str.encode(v, 'ascii'))
        if body:
            h.update(body)
        return self.hotkey.verify(h.hexdigest(), self.signature)