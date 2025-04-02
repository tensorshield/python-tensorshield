import hashlib
import pathlib
import time
from typing import AsyncGenerator

import httpx
from libcanonical.types import DomainName
from libcanonical.types import HTTPResourceLocator
from libtensorshield.types import SS58Address
from tensorshield.ext.wallet import Hotkey

from tensorshield.ext.iam.types import InvalidSignature
from tensorshield.ext.iam.types import MissingSignature


class HTTPHotkeySigned(httpx.Auth):
    hash_algorithm: str = 'sha256'
    hotkey: Hotkey
    netuid: int | None = None
    network: str | None = None

    @classmethod
    def fromwallet(
        cls,
        name: str,
        hotkey: str,
        netuid: int | None = None,
        network: str | None = None,
        wallet_path: pathlib.Path | str = '~/.bittensor/wallets' 
    ): # pragma: no cover
        if not isinstance(wallet_path, pathlib.Path):
            wallet_path = pathlib.Path(wallet_path)
        wallet_path = wallet_path.expanduser()
        key = Hotkey.model_validate({'name': name, 'hotkey': hotkey})
        key.load(wallet_path, mode='public')
        return cls(hotkey=key, netuid=netuid, network=network)

    def __init__(
        self,
        hotkey: Hotkey,
        netuid: int | None = None,
        network: str | None = None,
        audience: SS58Address | DomainName | HTTPResourceLocator | None = None
    ):
        self.audience = audience
        self.hotkey = hotkey
        self.netuid = netuid
        self.network = network

    async def async_auth_flow(
        self,
        request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        audience = self.audience or request.headers.get('X-Bittensor-Audience')
        nonce = time.monotonic_ns()
        headers: dict[str, str] = {}
        headers.update({
            'X-Bittensor-Nonce': str(nonce),
            'X-Bittensor-Hotkey': self.hotkey.ss58_address
        })

        netuid = request.headers.get('X-Bittensor-Subnet-ID') or self.netuid
        network = request.headers.get('X-Bittensor-Network') or self.network
        if netuid and network:
            headers.update({
                'X-Bittensor-Network': network,
                'X-Bittensor-Subnet-ID': str(netuid)
            })
        if audience is not None:
            headers['X-Bittensor-Audience'] = audience
        h = hashlib.new(name=self.hash_algorithm)

        for name, value in sorted(headers.items(), key=lambda x: x[0]):
            name = str.lower(name)
            h.update(str.encode(name, encoding='ascii'))
            h.update(str.encode(value, encoding='ascii'))
        if request.content:
            h.update(request.content)

        headers['Authorization'] = f'BT-SR25519-{str.upper(self.hash_algorithm)} {await self.sign(h.hexdigest())}'
        request.headers.update(headers)
        response = yield request
        if 200 <= response.status_code < 300 and SS58Address.is_valid(audience):
            # If the audience is a SS58Address, then the receiver must
            # sign the response. Only the response body is verified - it
            # is assumed that axons add their own information to the synapse,
            # more specifically a timestamp, so that responses can not be
            # replayed by other miners. TODO: This currently does not work
            # for streaming responses.
            h = hashlib.new(self.hash_algorithm)
            if response.headers.get('Content-Length'):
                h.update(await response.aread())
            audience = SS58Address(audience)
            signature = response.headers.get('X-Bittensor-Signature')
            if not await self.verify(
                audience=audience,
                message=h.digest(),
                signature=signature
            ):
                match (signature is None):
                    case True:
                        raise MissingSignature(
                            f'{audience} did not sign the response.'
                        )
                    case False:
                        raise InvalidSignature(
                            f'The response was not signed by {audience} or '
                            'has been tampered with.'
                        )

    async def verify(
        self,
        audience: SS58Address,
        message: bytes,
        signature: str | bytes | None
    ) -> bool:
        if signature is None:
            return False
        if isinstance(signature, str):
            try:
                signature = bytes.fromhex(signature)
            except ValueError:
                return False
        return audience.verify(message, signature)

    async def sign(self, message: str):
        return bytes.hex(await self.hotkey.sign(message.encode('ascii')))