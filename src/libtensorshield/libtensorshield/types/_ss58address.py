import functools
from typing import Any
from typing import TypeVar

from substrateinterface.utils.ss58 import ss58_decode
from substrateinterface.utils.ss58 import ss58_encode
from substrateinterface.utils.ss58 import is_valid_ss58_address
from substrateinterface import Keypair
from pydantic_core import CoreSchema
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
from pydantic import GetJsonSchemaHandler


__all__: list[str] = [
    'SS58Address'
]

T = TypeVar('T', bound='SS58Address')


class SS58Address(str):
    __module__: str = 'tensorshield.types'

    @classmethod
    def __get_pydantic_core_schema__(cls, *_: Any) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.chain_schema([
                core_schema.is_instance_schema(str),
                core_schema.no_info_plain_validator_function(cls.validate)
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(cls.serialize)
        )

    @classmethod
    def frombytes(cls, value: bytes):
        return cls(ss58_encode(value))

    @functools.cached_property
    def public_bytes(self):
        return bytes.fromhex(ss58_decode(self))

    @functools.cached_property
    def keypair(self):
        return Keypair(ss58_address=self)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _: CoreSchema,
        handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())

    @classmethod
    def validate(cls: type[T], instance: T | str) -> T:
        if not is_valid_ss58_address(instance):
            raise ValueError("not a valid SS58 address")
        return cls(instance)

    def serialize(self) -> str:
        return self

    def verify(
        self,
        data: str | bytes,
        signature: str | bytes
    ):
        return self.keypair.verify(data, signature)

    def __repr__(self): # pragma: no cover
        return f'<SS58Address: {str(self)}>'