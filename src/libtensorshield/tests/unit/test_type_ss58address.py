import os
import json

import pydantic
import pytest

from libtensorshield.types import SS58Address


class Model(pydantic.BaseModel):
    ss58_address: SS58Address


def test_get_model_validate():
    k = os.urandom(32)
    ck = SS58Address.frombytes(k)
    Model.model_validate({'ss58_address': ck})


def test_model_validate_json():
    k = os.urandom(32)
    ck = SS58Address.frombytes(k)
    Model.model_validate_json(json.dumps({'ss58_address': str(ck)}))


def test_serialize():
    adapter: pydantic.TypeAdapter[SS58Address] = pydantic.TypeAdapter(SS58Address)
    k = os.urandom(32)
    ck = SS58Address.frombytes(k)
    adapter.dump_python(ck)


def test_serialize_json():
    adapter: pydantic.TypeAdapter[SS58Address] = pydantic.TypeAdapter(SS58Address)
    k = os.urandom(32)
    ck = SS58Address.frombytes(k)
    adapter.dump_json(ck)


@pytest.mark.parametrize("value", ['foo'])
def test_invalid_input(value: str):
    adapter: pydantic.TypeAdapter[SS58Address] = pydantic.TypeAdapter(SS58Address)
    try:
        adapter.validate_python(value)
        assert False
    except ValueError:
        pass


def test_generate_json_schema():
    adapter: pydantic.TypeAdapter[SS58Address] = pydantic.TypeAdapter(SS58Address)
    adapter.json_schema()