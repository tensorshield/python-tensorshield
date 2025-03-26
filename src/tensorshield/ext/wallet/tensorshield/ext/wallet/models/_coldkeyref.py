import pathlib

import pydantic

from ._hotkey import Hotkey


class ColdkeyRef(pydantic.BaseModel):
    name: str = pydantic.Field(
        default=...
    )

    def hotkeys(
        self,
        wallet_path: pathlib.Path,
        refs_only: bool = True
    ):
        if not refs_only:
            raise NotImplementedError
        hotkeys: list[Hotkey] = []
        for p in sorted(wallet_path.joinpath(self.name).glob('hotkeys/*')):
            hotkeys.append(
                Hotkey.model_validate({
                    'name': self.name,
                    'hotkey': p.stem
                })
            )
        return hotkeys

    def __hash__(self):
        return hash(self.name)