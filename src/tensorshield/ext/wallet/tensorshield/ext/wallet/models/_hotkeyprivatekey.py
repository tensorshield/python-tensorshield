import pydantic
from cryptography.hazmat.primitives.asymmetric import ed25519
from libcanonical.types import HexEncoded

from ._hotkeypublickey import HotkeyPublicKey


class HotkeyPrivateKey(HotkeyPublicKey):
    private_key: HexEncoded = pydantic.Field(
        default=...,
        alias='privateKey'
    )

    @property
    def private(self):
        return ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key)