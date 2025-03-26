import ipaddress
import re
import pathlib
import sys
import warnings
from typing import Any

import pydantic
from libcanonical.bases import EnvironmentBaseModel
from libcanonical.types import ColonSeparatedList
from libcanonical.types import HTTPResourceLocator
from libcanonical.types import WebSocketResourceLocator

from tensorshield.ext.wallet import ColdkeyRef
from tensorshield.ext.wallet import Hotkey

from ._const import FINNEY_ENTRYPOINT
from ._const import CHAIN_ENDPOINT_NETWORKS
from ._const import NETWORK_CHAIN_ENDPOINTS


class Environment(EnvironmentBaseModel):
    axon_ip: ipaddress.IPv4Address = pydantic.Field(
        default=ipaddress.IPv4Address('0.0.0.0'),
        alias='BT_AXON_HOST'
    )

    axon_port: int = pydantic.Field(
        default=8091,
        alias='BT_AXON_PORT',
        gt=1000
    )

    axon_disabled: bool = pydantic.Field(
        default=False,
        alias='BT_AXON_DISABLED'
    )

    chain_endpoint: HTTPResourceLocator | WebSocketResourceLocator | None = pydantic.Field(
        default=None,
        alias='BT_SUBTENSOR_CHAIN_ENDPOINT'
    )

    enabled_hotkeys: ColonSeparatedList[Hotkey] = pydantic.Field(
        default_factory=ColonSeparatedList,
        alias='BT_ENABLED_HOTKEYS'
    )

    network: str = pydantic.Field(
        default='finney',
        alias='BT_NETWORK'
    )

    netuid: int | None = pydantic.Field(
        default=None,
        alias='BT_SUBNET_UID'
    )

    force_validator_permit: bool = pydantic.Field(
        default=True,
        alias='BT_FORCE_VALIDATOR_PERMIT'
    )

    validator_min_stake: int = pydantic.Field(
        default=4096,
        alias='BT_VALIDATOR_MIN_STAKE'
    )

    wallet_path: pathlib.Path = pydantic.Field(
        default=pathlib.Path('~/.bittensor/wallets').expanduser(),
        alias='BT_WALLET_PATH'
    )

    @pydantic.field_validator('enabled_hotkeys', mode='after')
    def preprocess_enabled_hotkeys(cls, value: list[Hotkey | ColdkeyRef | str] | None):
        if value is not None:
            for i, item in enumerate(value):
                if isinstance(item, (ColdkeyRef, Hotkey)):
                    continue
                match item:
                    case 'all': continue
                    case _:
                        name, *hotkey = str.split(item, '/')
                        match len(hotkey):
                            case 0:
                                value[i] = ColdkeyRef(name=name)
                            case 1:
                                value[i] = Hotkey.model_validate({
                                    'name': name,
                                    'hotkey': hotkey[0]
                                })
                            case _:
                                raise ValueError("invalid format")
        return value

    @pydantic.field_validator('wallet_path', mode='after')
    def validate_wallet_path(cls, value: str) -> str:
        #cls.validate_directory(value, False) # type: ignore
        return value

    @pydantic.model_validator(mode='before')
    def validate_network(cls, values: dict[str, Any]) -> dict[str, Any]:
        chain_endpoint = values.get('chain_endpoint')
        network = values.get('network')
        match network:
            case None:
                chain_endpoint = chain_endpoint or FINNEY_ENTRYPOINT
                network = CHAIN_ENDPOINT_NETWORKS.get(chain_endpoint)
            case _:
                chain_endpoint = chain_endpoint or NETWORK_CHAIN_ENDPOINTS.get(network)
                if not chain_endpoint:
                    raise ValueError(
                        "Provide either BT_SUBNET with a known named network "
                        "or set the BT_CHAIN_ENDPOINT variable."
                    )
                warnings.warn(
                    f"BT_SUBNET specifies unknown network '{network}', "
                    f"but is overridden by BT_CHAIN_ENDPOINT: {chain_endpoint}",
                    UserWarning
                )
        values.update({
            'chain_endpoint': chain_endpoint,
            'network': network
        })
        return values

    @pydantic.model_validator(mode='after')
    def postprocess(self):
        hotkeys: list[Hotkey | ColdkeyRef | str] = list(self.enabled_hotkeys)
        if len(self.enabled_hotkeys) == 1 and hotkeys[0] == 'all': # type: ignore
            hotkeys = []
            for path in self.wallet_path.glob('*/hotkeys/*'):
                m = re.match(r'.*/([\d\w]+)/hotkeys/([\d\w]+)$', str(path))
                if m is None:
                    sys.stderr.write(f"Unsupported hotkey filepath: {path}")
                    sys.stderr.flush()
                    raise SystemExit(1)
                name, hotkey = m.groups()
                hotkeys.append(
                    Hotkey.model_validate({
                        'name': name,
                        'hotkey': hotkey
                    })
                )

        coldkeyrefs = [ref for ref in hotkeys if isinstance(ref, ColdkeyRef)]
        for ref in coldkeyrefs:
            hotkeys.pop(hotkeys.index(ref))
            hotkeys.extend(ref.hotkeys(self.wallet_path, refs_only=True))

        self.enabled_hotkeys = ColonSeparatedList(  # type: ignore
            sorted(hotkeys, key=lambda ref: ref.qualname) # type: ignore
        )
        assert all([isinstance(hotkey, Hotkey) for hotkey in hotkeys])
        return self