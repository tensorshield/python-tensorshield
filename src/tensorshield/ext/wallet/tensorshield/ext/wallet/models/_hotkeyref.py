import pydantic


class HotkeyRef(pydantic.BaseModel):
    model_config = {'populate_by_name': True}

    name: str = pydantic.Field(
        default=...
    )

    hotkey: str = pydantic.Field(
        default=...
    )

    @property
    def qualname(self):
        return f'{self.name}/{self.hotkey}'

    def __hash__(self):
        return hash(f'{self.name}/{self.hotkey}')