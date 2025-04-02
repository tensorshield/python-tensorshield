import pydantic
from libcanonical.types import HexEncoded
from substrateinterface import Keypair

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
        return Keypair(public_key=self.public_key, ss58_format=42)

    def verify(
        self,
        message: str | bytes,
        signature: str | bytes,
        encoding: str = 'utf-8'
    ) -> bool:
        if isinstance(message, str):
            message = str.encode(message, encoding=encoding)
        if isinstance(signature, str):
            signature = str.encode(signature, encoding=encoding)
        return self.public.verify(bytes(message), bytes(signature))