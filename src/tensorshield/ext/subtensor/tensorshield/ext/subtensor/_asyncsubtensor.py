import logging
import os
import ssl
import sys
from typing import Any

import asyncstdlib
from async_substrate_interface import AsyncSubstrateInterface


os.environ.setdefault('BT_SS58_FORMAT', '42')
if not os.environ['BT_SS58_FORMAT'].isdigit():
    sys.stdout.write("BT_SS58_FORMAT must be an integer.")
    sys.stdout.flush()
    raise SystemExit(1)
SS58_FORMAT = int(os.environ['BT_SS58_FORMAT'])


class AsyncSubtensor:
    """Thin layer for interacting with Substrate Interface. Mostly a collection
    of frequently-used calls.
    """
    logger: logging.Logger = logging.getLogger(__name__)
    ss58_format: int = SS58_FORMAT
    substrate: AsyncSubstrateInterface
    type_registry: dict[str, dict[str, str]] = {
        "types": {
            "Balance": "u64",  # Need to override default u128
        },
    }

    def __init__(self, chain_endpoint: str, _mock: bool = False):
        self.chain_endpoint = chain_endpoint
        self.substrate = AsyncSubstrateInterface(
            url=self.chain_endpoint,
            ss58_format=self.ss58_format,
            type_registry=self.type_registry,
            use_remote_preset=True,
            chain_name="Bittensor",
            _mock=_mock,
        )

    async def connect(self):
        await self.initialize()

    async def close(self):
        """Close the connection."""
        if self.substrate:
            await self.substrate.close()

    async def determine_block_hash(
        self,
        block: int | None,
        block_hash: str | None = None,
        reuse_block: bool = False,
    ) -> str | None:
        # Ensure that only one of the parameters is specified.
        if sum(bool(x) for x in [block, block_hash, reuse_block]) > 1: # type: ignore
            raise ValueError(
                "Only one of `block`, `block_hash`, or `reuse_block` can be specified."
            )

        # Return the appropriate value.
        if block_hash:
            return block_hash
        if block:
            return await self.get_block_hash(block)
        return None

    async def initialize(self):
        self.logger.info(
            f"[magenta]Connecting to Substrate:[/magenta] [blue]{self}[/blue][magenta]...[/magenta]"
        )
        try:
            await self.substrate.initialize()
            return self
        except TimeoutError:
            self.logger.error(
                f"[red]Error[/red]: Timeout occurred connecting to substrate."
                f" Verify your chain and network settings: {self}"
            )
            raise ConnectionError
        except (ConnectionRefusedError, ssl.SSLError) as error:
            self.logger.error(
                "Connection refused when connecting to substrate. "
                "Verify your chain and network settings: %s. Error: %s",
                repr(self),
                repr(error)
            )
            raise ConnectionError

    async def get_block_hash(self, block: int | None = None) -> str:
        """
        Retrieves the hash of a specific block on the Bittensor blockchain.
        The block hash is a unique identifier representing the cryptographic
        hash of the block's content, ensuring its integrity and immutability.

        Arguments:
            block (int): The block number for which the hash is to be
                retrieved.

        Returns:
            str: The cryptographic hash of the specified block.

        The block hash is a fundamental aspect of blockchain technology,
        providing a secure reference to each block's data. It is crucial
        for verifying transactions, ensuring data consistency, and
        maintaining the trustworthiness of the blockchain.
        """
        if block:
            return await self._get_block_hash(block) # type: ignore
        else:
            return await self.substrate.get_chain_head()

    async def query_runtime_api(
        self,
        runtime_api: str,
        method: str,
        params: list[Any] | dict[str, Any] | None,
        block: int | None = None,
        block_hash: str | None = None,
        reuse_block: bool = False,
    ) -> Any | None:
        """
        Queries the runtime API of the Bittensor blockchain, providing a way to interact with the underlying runtime and
            retrieve data encoded in Scale Bytes format. This function is essential for advanced users who need to
            interact with specific runtime methods and decode complex data types.

        Args:
            runtime_api: The name of the runtime API to query.
            method: The specific method within the runtime API to call.
            params: The parameters to pass to the method call.
            block: the block number for this query. Do not specify if using block_hash or reuse_block
            block_hash: The hash of the blockchain block number at which to perform the query. Do not specify if
                using block or reuse_block
            reuse_block: Whether to reuse the last-used block hash. Do not set if using block_hash or block

        Returns:
            The decoded result from the runtime API call, or `None` if the call fails.

        This function enables access to the deeper layers of the Bittensor blockchain, allowing for detailed and
            specific interactions with the network's runtime environment.
        """
        block_hash = await self.determine_block_hash(block, block_hash, reuse_block)
        if not block_hash and reuse_block:
            block_hash = self.substrate.last_block_hash
        result = await self.substrate.runtime_call( # type: ignore
            runtime_api, method, params, block_hash
        )
        return result.value # type: ignore

    @asyncstdlib.lru_cache(maxsize=128)
    async def _get_block_hash(self, block_id: int) -> str:
        return await self.substrate.get_block_hash(block_id) # type: ignore