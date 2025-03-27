from typing import Optional

import pydantic


def _cast_int(raw: str | None) -> int | None:
    return int(raw) if raw is not None else raw


def _cast_float(raw: str | None) -> float | None:
    return float(raw) if raw is not None else raw


class TerminalInfo(pydantic.BaseModel):
    """
    TerminalInfo encapsulates detailed information about a network synapse (node)
    involved in a communication process.

    This class serves as a metadata carrier,
    providing essential details about the state and configuration of a terminal
    during network interactions. This is a crucial class in the Bittensor
    framework.

    The TerminalInfo class contains information such as HTTP status codes
    and messages, processing times, IP addresses, ports, Bittensor version
    numbers, and unique identifiers. These details are vital for maintaining
    network reliability, security, and efficient data flow within the
    Bittensor network.

    This class includes Pydantic validators and root validators to enforce
    data integrity and format. It is designed to be used natively within
    Synapses, so that you will not need to call this directly, but rather
    is used as a helper class for Synapses.

    Args:
        status_code (int): HTTP status code indicating the result of a network
            request. Essential for identifying the outcome of network
            interactions.
        status_message (str): Descriptive message associated with the status
            code, providing additional context about the request's result.
        process_time (float): Time taken by the terminal to process the call,
            important for performance monitoring and optimization.
        ip (str): IP address of the terminal, crucial for network routing
            and data transmission.
        port (int): Network port used by the terminal, key for establishing
            network connections.
        version (int): Bittensor version running on the terminal, ensuring
            compatibility between different nodes in the network.
        nonce (int): Unique, monotonically increasing number for each terminal,
            aiding in identifying and ordering network interactions.
        uuid (str): Unique identifier for the terminal, fundamental for network
            security and identification.
        hotkey (str): Encoded hotkey string of the terminal wallet, important
            for transaction and identity verification in the network.
        signature (str): Digital signature verifying the tuple of nonce,
            axon_hotkey, dendrite_hotkey, and uuid,
            critical for ensuring data authenticity and security.

    Usage::

        # Creating a TerminalInfo instance
        from bittensor.core.synapse import TerminalInfo

        terminal_info = TerminalInfo(
            status_code=200,
            status_message="Success",
            process_time=0.1,
            ip="198.123.23.1",
            port=9282,
            version=111,
            nonce=111111,
            uuid="5ecbd69c-1cec-11ee-b0dc-e29ce36fec1a",
            hotkey="5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1",
            signature="0x0813029319030129u4120u10841824y0182u091u230912u"
        )

        # Accessing TerminalInfo attributes
        ip_address = terminal_info.ip
        processing_duration = terminal_info.process_time

        # TerminalInfo can be used to monitor and verify network interactions, ensuring proper communication and
        security within the Bittensor network.

    TerminalInfo plays a pivotal role in providing transparency and control over network operations, making it an
    indispensable tool for developers and users interacting with the Bittensor ecosystem.
    """

    model_config = pydantic.ConfigDict(validate_assignment=True)

    # The HTTP status code from: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
    status_code: Optional[int] = pydantic.Field(
        title="status_code",
        description="The HTTP status code from: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
        examples=[200],
        default=None,
        frozen=False,
    )

    # The HTTP status code from: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
    status_message: Optional[str] = pydantic.Field(
        title="status_message",
        description="The status_message associated with the status_code",
        examples=["Success"],
        default=None,
        frozen=False,
    )

    # Process time on this terminal side of call
    process_time: Optional[float] = pydantic.Field(
        title="process_time",
        description="Process time on this terminal side of call",
        examples=[0.1],
        default=None,
        frozen=False,
    )

    # The terminal ip.
    ip: Optional[str] = pydantic.Field(
        title="ip",
        description="The ip of the axon receiving the request.",
        examples=["198.123.23.1"],
        default=None,
        frozen=False,
    )

    # The host port of the terminal.
    port: Optional[int] = pydantic.Field(
        title="port",
        description="The port of the terminal.",
        examples=["9282"],
        default=None,
        frozen=False,
    )

    # The bittensor version on the terminal as an int.
    version: Optional[int] = pydantic.Field(
        title="version",
        description="The bittensor version on the axon as str(int)",
        examples=[111],
        default=None,
        frozen=False,
    )

    # A Unix timestamp to associate with the terminal
    nonce: Optional[int] = pydantic.Field(
        title="nonce",
        description="A Unix timestamp that prevents replay attacks",
        examples=[111111],
        default=None,
        frozen=False,
    )

    # A unique identifier associated with the terminal, set on the axon side.
    uuid: Optional[str] = pydantic.Field(
        title="uuid",
        description="A unique identifier associated with the terminal",
        examples=["5ecbd69c-1cec-11ee-b0dc-e29ce36fec1a"],
        default=None,
        frozen=False,
    )

    # The bittensor version on the terminal as an int.
    hotkey: Optional[str] = pydantic.Field(
        title="hotkey",
        description="The ss58 encoded hotkey string of the terminal wallet.",
        examples=["5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1"],
        default=None,
        frozen=False,
    )

    # A signature verifying the tuple (axon_nonce, axon_hotkey, dendrite_hotkey, axon_uuid)
    signature: Optional[str] = pydantic.Field(
        title="signature",
        description="A signature verifying the tuple (nonce, axon_hotkey, dendrite_hotkey, uuid)",
        examples=["0x0813029319030129u4120u10841824y0182u091u230912u"],
        default=None,
        frozen=False,
    )

    # Extract the process time on this terminal side of call as a float
    _extract_process_time = pydantic.field_validator("process_time", mode="before")(_cast_float)

    # Extract the host port of the terminal as an int
    _extract_port = pydantic.field_validator("port", mode="before")(_cast_int)

    # Extract the bittensor version on the terminal as an int.
    _extract_version = pydantic.field_validator("version", mode="before")(_cast_int)

    # Extract the Unix timestamp associated with the terminal as an int
    _extract_nonce = pydantic.field_validator("nonce", mode="before")(_cast_int)

    # Extract the HTTP status code as an int
    _extract_status_code = pydantic.field_validator("status_code", mode="before")(_cast_int)