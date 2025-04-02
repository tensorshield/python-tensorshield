import pytest
import pydantic
from pydantic.json_schema import models_json_schema

from tensorshield.ext.iam.types import AuthorizationHeader


@pytest.mark.parametrize("value", [
    AuthorizationHeader.validate("BT-SR25519-SHA256 abc")
])
def test_adapter_dump(value: AuthorizationHeader):
    adapter = pydantic.TypeAdapter(AuthorizationHeader)
    adapter.dump_json(value)
    adapter.dump_python(value)


@pytest.mark.parametrize("value", [
    "BT-SR25519-SHA256 abc"
])
def test_adapter_validate(value: str):
    adapter = pydantic.TypeAdapter(AuthorizationHeader)
    adapter.validate_python(value)
    adapter.validate_json(f'"{value}"')


@pytest.mark.parametrize("value", [
    "BT-SR25519-SHA256",
    "Unknown Schema",
    "BT-ABC3-SHA234 v",
    "BT-SR25519-SHA123 abc",
])
def test_adapter_validate_invalid(value: str):
    adapter = pydantic.TypeAdapter(AuthorizationHeader)
    with pytest.raises(ValueError):
        adapter.validate_python(value)


def test_generate_schema():
    class Model(pydantic.BaseModel):
        v: AuthorizationHeader

    models_json_schema([(Model, 'validation')])
    models_json_schema([(Model,  'serialization')])
