import pydantic
from libcanonical.types import HexEncoded
from starlette.datastructures import Headers

from libtensorshield.types import SS58Address


class SynapseHeader(pydantic.BaseModel):
    accept: str | None = pydantic.Field(
        default=None,
        alias='accept'
    )

    content_type: str = pydantic.Field(
        default=...,
        alias='content-type'
    )

    user_agent: str | None = pydantic.Field(
        default=None,
        alias='user-agent'
    )

    accept_encoding: str | None = pydantic.Field(
        default=None,
        alias='accept-encoding'
    )

    version: str = pydantic.Field(
        default='tensorshield.ai/v1',
        alias='bt_version'
    )

    dendrite_hotkey: SS58Address = pydantic.Field(
        default=...,
        alias='bt_header_dendrite_hotkey'
    )

    dendrite_ip: str = pydantic.Field(
        default=...,
        alias='bt_header_dendrite_ip'
    )

    dendrite_nonce: int = pydantic.Field(
        default=...,
        alias='bt_header_dendrite_nonce'
    )

    dendrite_signature: HexEncoded = pydantic.Field(
        default=...,
        alias='bt_header_dendrite_signature'
    )

    dendrite_uuid: str = pydantic.Field(
        default=...,
        alias='bt_header_dendrite_uuid'
    )

    dendrite_version: str = pydantic.Field(
        default=...,
        alias='bt_header_dendrite_version'
    )

    axon_hotkey: SS58Address = pydantic.Field(
        default=...,
        alias='bt_header_axon_hotkey'
    )

    axon_ip: str = pydantic.Field(
        default=...,
        alias='bt_header_axon_ip'
    )

    axon_port: int = pydantic.Field(
        default=...,
        alias='bt_header_axon_port'
    )

    forwared_for: str | None = pydantic.Field(
        default=None,
        alias='x-forwarded-for'
    )

    forwared_protocol: str | None = pydantic.Field(
        default=None,
        alias='x-forwarded-proto'
    )

    computed_body_hash: str = pydantic.Field(
        default=...,
        alias='computed_body_hash'
    )

    subnet_uid: int | None = pydantic.Field(
        default=None,
        alias='bittensor-subnet-uid'
    )

    timeout: float = pydantic.Field(
        default=...,
        alias='timeout'
    )

    @classmethod
    def model_validate_headers(cls, headers: Headers):
        return cls.model_validate(headers)

    def model_dump_headers(self):
        headers = self.model_dump(
            by_alias=True,
            exclude_none=True
        )
        return {k: str(v) for k, v in headers.items()}