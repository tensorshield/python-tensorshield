import pydantic
from libcanonical.types import AwaitableBytes
from libcanonical.types import HexEncoded
from substrateinterface import Keypair

from ._hotkeypublickey import HotkeyPublicKey


class HotkeyPrivateKey(HotkeyPublicKey):
    private_key: HexEncoded = pydantic.Field(
        default=...,
        alias='privateKey'
    )

    @property
    def private(self):
        if len(self.private_key) != 64:
            raise ValueError(f"Invalid private key length: {len(self.private_key)}")
        return Keypair(private_key=self.private_key, ss58_format=42)

    @property
    def private_hex(self):
        return f'0x{bytes.hex(self.private_key)}'

    def sign(self, message: bytes | str, encoding: str = 'utf-8'):
        if isinstance(message, str):
            message = str.encode(message, encoding)
        return AwaitableBytes(self.private.sign(message))