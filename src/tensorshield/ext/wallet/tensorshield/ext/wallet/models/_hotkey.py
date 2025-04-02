import json
import os
import pathlib
from typing import Literal

import pydantic
from substrateinterface import Keypair
from libtensorshield.types import SS58Address

from ._hotkeyref import HotkeyRef
from ._hotkeyprivatekey import HotkeyPrivateKey
from ._hotkeypublickey import HotkeyPublicKey


class Hotkey(pydantic.RootModel[HotkeyPrivateKey | HotkeyPublicKey | HotkeyRef]):

    @property
    def public_bytes(self):
        if not isinstance(self.root, (HotkeyPublicKey, HotkeyPrivateKey)):
            raise TypeError("Hotkey is not loaded.")
        return self.root.public_key

    @property
    def hotkey(self):
        return self.root.hotkey

    @property
    def name(self):
        return self.root.name

    @property
    def qualname(self):
        return f'{self.root.name}/{self.root.hotkey}'

    @property
    def private_hex(self):
        if not isinstance(self.root, HotkeyPrivateKey):
            raise TypeError(f"Private key not available: {type(self.root).__name__}")
        return self.root.private_hex

    @property
    def private_bytes(self):
        if not isinstance(self.root, HotkeyPrivateKey):
            raise TypeError(f"Private key not available: {type(self.root).__name__}")
        return self.root.private_key

    @property
    def ss58_address(self):
        if not isinstance(self.root, (HotkeyPublicKey, HotkeyPrivateKey)):
            raise TypeError("Hotkey is not loaded.")
        return self.root.ss58_address

    @classmethod
    def generate(cls, name: str, hotkey: str):
        private = Keypair.create_from_mnemonic(Keypair.generate_mnemonic(), ss58_format=42)
        return cls.model_validate({
            'name': name,
            'hotkey': hotkey,
            'private_key': private.private_key,
            'public_key': private.public_key,
            'ss58_address': SS58Address(private.ss58_address)
        })

    def load(
        self,
        path: pathlib.Path,
        mode: Literal['public', 'private', 'phrase']
    ):
        p = path.joinpath(self.root.name, 'hotkeys', self.root.hotkey)
        with open(p, 'r') as f:
            data: dict[str, str] = {
                **json.loads(f.read()),
                'name': self.root.name,
                'hotkey': self.root.hotkey
            }
        match mode:
            case 'public': self.root = HotkeyPublicKey.model_validate(data)
            case 'private': self.root = HotkeyPrivateKey.model_validate(data)
            case 'phrase': raise NotImplementedError

        # TODO: Use stringwipe instead of garbage collect.
        del data

    def sign(
        self,
        message: str | bytes,
        encoding: str = 'utf-8',
        blocking: bool = False
    ):
        if not isinstance(self.root, HotkeyPrivateKey):
            raise TypeError("Hotkey is not loaded as a signing key.")
        return self.root.sign(message, encoding=encoding)

    def verify(self, message: str | bytes, data: str | bytes, encoding: str = 'utf-8') -> bool:
        if not isinstance(self.root, (HotkeyPrivateKey, HotkeyPublicKey)):
            raise TypeError("Public key not available.")
        return self.root.verify(message, data, encoding)

    def unload(self):
        self.root = HotkeyRef.model_validate(self.root.model_dump())

    def __hash__(self):
        return hash(self.root)