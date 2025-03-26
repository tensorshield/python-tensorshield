import json
import pathlib
from typing import Literal

import pydantic

from ._hotkeyref import HotkeyRef
from ._hotkeyprivatekey import HotkeyPrivateKey
from ._hotkeypublickey import HotkeyPublicKey


class Hotkey(pydantic.RootModel[HotkeyRef|HotkeyPublicKey]):

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
    def ss58_address(self):
        if not isinstance(self.root, (HotkeyPublicKey, HotkeyPrivateKey)):
            raise TypeError("Hotkey is not loaded.")
        return self.root.ss58_address

    @property
    def qualname(self):
        return f'{self.root.name}/{self.root.hotkey}'

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

    def unload(self):
        self.root = HotkeyRef.model_validate(self.root.model_dump())

    def __hash__(self):
        return hash(self.root)