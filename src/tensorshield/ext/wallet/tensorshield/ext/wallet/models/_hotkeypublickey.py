import pydantic
from cryptography.hazmat.primitives.asymmetric import ed25519
from libcanonical.types import HexEncoded

from libtensorshield.types import SS58Address
from ._hotkeyref import HotkeyRef


class HotkeyPublicKey(HotkeyRef):
    public_key: HexEncoded = pydantic.Field(
        default=...,
        alias='publicKey'
    )

    ss58_address: SS58Address = pydantic.Field(
        default=...,
        alias='ss58Address'
    )

    @property
    def public(self):
        return ed25519.Ed25519PublicKey.from_public_bytes(self.public_key)