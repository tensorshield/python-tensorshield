import re
from typing import Any
from typing import TypeVar

from pydantic_core import CoreSchema
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
from pydantic import GetJsonSchemaHandler


__all__: list[str] = [
    'AuthorizationHeader'
]

T = TypeVar('T', bound='AuthorizationHeader')


class AuthorizationHeader:
    __module__: str = 'tensorshield.ext.iam.types'
    scheme: str
    digest_algorithm: str

    @classmethod
    def __get_pydantic_core_schema__(cls, *_: Any) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.chain_schema([
                    core_schema.is_instance_schema(str),
                    core_schema.no_info_plain_validator_function(cls.validate)
                ]),
                core_schema.is_instance_schema(cls)
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(cls.serialize)
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _: CoreSchema,
        handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())

    @classmethod
    def validate(cls: type[T], v: str) -> T:
        try:
            scheme, value = str.split(v, ' ')
        except ValueError:
            raise ValueError('malformed Authorization header')
        if not (m := re.match(r'(BT\-[\d\w]+\-[\d\w]+)', scheme)):
            raise ValueError('unknown authentication scheme')
        scheme = m.group(1)
        digest_algorithm: str | None = None
        match scheme:
            case 'BT-SR25519-SHA256':
                digest_algorithm = 'sha256'
            case _:
                raise ValueError(f"unknown scheme: {scheme}")
        if not digest_algorithm: # pragma: no cover
            raise ValueError(f"unknown scheme: {scheme}")
        return cls(scheme, str.lower(digest_algorithm), value)

    def __init__(self, scheme: str, digest_algorithm: str, signature: str):
        self.scheme = scheme
        self.digest_algorithm = digest_algorithm
        self.signature = signature

    @staticmethod
    def serialize(v: 'AuthorizationHeader'):
        return f'{v.scheme} {v.signature}'

    def __repr__(self): # pragma: no cover
        return f'<Authorization: {self.scheme}>'