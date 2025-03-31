"""
This module defines the `AxonInfo` class, a data structure used to represent information about an axon endpoint
in the bittensor network.
"""
import ipaddress
from dataclasses import asdict, dataclass
from typing import Any
from typing import TypeVar
from typing import Union

from async_substrate_interface.utils import json

from ._infobase import InfoBase


T = TypeVar('T', bound='AxonInfo')


@dataclass
class AxonInfo(InfoBase):
    """
    The `AxonInfo` class represents information about an axon endpoint in the bittensor network. This includes
    properties such as IP address, ports, and relevant keys.

    Attributes:
        version (int): The version of the axon endpoint.
        ip (str): The IP address of the axon endpoint.
        port (int): The port number the axon endpoint uses.
        ip_type (int): The type of IP protocol (e.g., IPv4 or IPv6).
        hotkey (str): The hotkey associated with the axon endpoint.
        coldkey (str): The coldkey associated with the axon endpoint.
        protocol (int): The protocol version (default is 4).
        placeholder1 (int): Reserved field (default is 0).
        placeholder2 (int): Reserved field (default is 0).
    """

    version: int
    ip: str
    port: int
    ip_type: int
    hotkey: str
    coldkey: str
    protocol: int = 4
    placeholder1: int = 0
    placeholder2: int = 0

    @property
    def is_serving(self) -> bool:
        """True if the endpoint is serving."""
        return self.ip != "0.0.0.0"

    def ip_str(self) -> str:
        """Return the whole IP as string"""
        if self.protocol != 4:
            raise NotImplementedError
        return f'{self.ip}:{self.port}'

    def __eq__(self, other: object):
        if other is None:
            return False

        if not isinstance(other, AxonInfo):
            return NotImplemented

        if (
            self.version == other.version
            and self.ip == other.ip
            and self.port == other.port
            and self.ip_type == other.ip_type
            and self.coldkey == other.coldkey
            and self.hotkey == other.hotkey
        ):
            return True

        return False

    def __str__(self):
        return f"AxonInfo( {self.ip_str()}, {self.hotkey}, {self.coldkey}, {self.version} )"

    def __repr__(self):
        return self.__str__()

    def to_string(self) -> str:
        """Converts the `AxonInfo` object to a string representation using JSON."""
        try:
            return json.dumps(asdict(self))
        except (TypeError, ValueError):
            return AxonInfo(0, "", 0, 0, "", "").to_string()

    @classmethod
    def _from_dict(cls: type[T], decoded: dict[str, Any]) -> T:
        """Returns a AxonInfo object from decoded chain data."""
        return cls(
            version=decoded["version"],
            ip=str(ipaddress.IPv4Address(int(decoded["ip"]))),
            port=decoded["port"],
            ip_type=decoded["ip_type"],
            placeholder1=decoded["placeholder1"],
            placeholder2=decoded["placeholder2"],
            protocol=decoded["protocol"],
            hotkey=decoded["hotkey"],
            coldkey=decoded["coldkey"],
        )

    @classmethod
    def from_string(cls, json_string: str) -> "AxonInfo":
        """
        Creates an `AxonInfo` object from its string representation using JSON.

        Args:
            json_string (str): The JSON string representation of the AxonInfo object.

        Returns:
            AxonInfo: An instance of AxonInfo created from the JSON string. If decoding fails, returns a default
                `AxonInfo` object with default values.

        Raises:
            json.JSONDecodeError: If there is an error in decoding the JSON string.
            TypeError: If there is a type error when creating the AxonInfo object.
            ValueError: If there is a value error when creating the AxonInfo object.
        """
        try:
            data = json.loads(json_string)
            return cls(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            return AxonInfo(0, "", 0, 0, "", "")

    @classmethod
    def from_neuron_info(cls, neuron_info: dict[str, Any]) -> "AxonInfo":
        """
        Converts a dictionary to an `AxonInfo` object.

        Args:
            neuron_info (dict): A dictionary containing the neuron information.

        Returns:
            instance (AxonInfo): An instance of AxonInfo created from the dictionary.
        """
        return cls(
            version=neuron_info["axon_info"]["version"],
            ip=str(ipaddress.IPv4Address(int(neuron_info["axon_info"]["ip"]))),
            port=neuron_info["axon_info"]["port"],
            ip_type=neuron_info["axon_info"]["ip_type"],
            hotkey=neuron_info["hotkey"],
            coldkey=neuron_info["coldkey"],
        )

    def to_parameter_dict(
        self,
    ) -> dict[str, Union[int, str]]:
        """Returns a torch tensor or dict of the subnet info, depending on the USE_TORCH flag set."""
        return self.__dict__

    @classmethod
    def from_parameter_dict(
        cls,
        parameter_dict: dict[str, Any]
    ) -> "AxonInfo":
        """Returns an axon_info object from a torch parameter_dict or a parameter dict."""
        return cls(**parameter_dict)
