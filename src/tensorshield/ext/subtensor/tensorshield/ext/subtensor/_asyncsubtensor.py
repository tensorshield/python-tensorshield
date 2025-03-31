import logging
import os
import ssl
import sys
from typing import cast
from typing import Any
from types import TracebackType

import asyncstdlib
from async_substrate_interface import AsyncSubstrateInterface
from libtensorshield.types import NeuronInfo

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

    async def get_current_block(self) -> int:
        """
        Returns the current block number on the Bittensor blockchain.
        This function provides the latest block number, indicating the
        most recent state of the blockchain.

        Returns:
            int: The current chain block number.

        Knowing the current block number is essential for querying real-time
            data and performing time-sensitive operations on the blockchain.
            It serves as a reference point for network activities and data
            synchronization.
        """
        return await self.substrate.get_block_number(None)

    async def get_hyperparameter(
        self,
        param_name: str,
        netuid: int,
        block: int | None = None,
        block_hash: str | None = None,
        reuse_block: bool = False,
        subnet_exists: bool = False
    ) -> Any | None:
        """
        Retrieves a specified hyperparameter for a specific subnet.

        Arguments:
            param_name (str): The name of the hyperparameter to retrieve.
            netuid (int): The unique identifier of the subnet.
            block: the block number at which to retrieve the hyperparameter. Do not specify if using block_hash or
                reuse_block
            block_hash (Optional[str]): The hash of blockchain block number for the query. Do not specify if using
                block or reuse_block
            reuse_block (bool): Whether to reuse the last-used block hash. Do not set if using block_hash or block.

        Returns:
            The value of the specified hyperparameter if the subnet exists, or None
        """
        block_hash = await self.determine_block_hash(block, block_hash, reuse_block)
        if not subnet_exists and not await self.subnet_exists(
            netuid, block_hash=block_hash, reuse_block=reuse_block
        ):
            raise ValueError(f"Subnet {netuid} does not exist.")

        result = await self.substrate.query( # type: ignore
            module="SubtensorModule",
            storage_function=param_name,
            params=[netuid],
            block_hash=block_hash,
            reuse_block_hash=reuse_block,
        )

        return getattr(result, "value", result)

    async def immunity_period(
        self,
        netuid: int,
        block: int | None = None,
        block_hash: str | None = None,
        reuse_block: bool = False,
    ) -> int | None:
        """
        Retrieves the 'ImmunityPeriod' hyperparameter for a specific subnet. This parameter
        defines the duration during which new neurons are protected from certain network
        penalties or restrictions.

        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            block_hash (Optional[str]): The blockchain block_hash representation of the block id.
            reuse_block (bool): Whether to reuse the last-used blockchain block hash.

        Returns:
            Optional[int]: The value of the 'ImmunityPeriod' hyperparameter if the subnet exists, ``None`` otherwise.

        The 'ImmunityPeriod' is a critical aspect of the network's governance system, ensuring that new participants
            have a grace period to establish themselves and contribute to the network without facing immediate
            punitive actions.
        """
        block_hash = await self.determine_block_hash(block, block_hash, reuse_block)
        call = await self.get_hyperparameter(
            param_name="ImmunityPeriod",
            netuid=netuid,
            block_hash=block_hash,
            reuse_block=reuse_block,
        )
        return None if call is None else int(call)

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

    async def neurons(
        self,
        netuid: int,
        block: int | None = None,
        block_hash: str | None = None,
        reuse_block: bool = False,
    ) -> list[NeuronInfo]:
        """
        Retrieves a list of all neurons within a specified subnet of the Bittensor network.
        This function provides a snapshot of the subnet's neuron population, including each neuron's attributes and
            network interactions.

        Arguments:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            block_hash (str): The hash of the blockchain block number for the query.
            reuse_block (bool): Whether to reuse the last-used blockchain block hash.

        Returns:
            A list of NeuronInfo objects detailing each neuron's characteristics in the subnet.

        Understanding the distribution and status of neurons within a subnet is key to comprehending the network's
            decentralized structure and the dynamics of its consensus and governance processes.
        """
        result = await self.query_runtime_api(
            runtime_api="NeuronInfoRuntimeApi",
            method="get_neurons",
            params=[netuid],
            block=block,
            block_hash=block_hash,
            reuse_block=reuse_block,
        )

        if not result:
            return cast(list[NeuronInfo], [])

        return NeuronInfo.list_from_dicts(result)

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
        Queries the runtime API of the Bittensor blockchain, providing a way to
        interact with the underlying runtime and retrieve data encoded in Scale
        Bytes format. This function is essential for advanced users who need to
        interact with specific runtime methods and decode complex data types.

        Args:
            runtime_api: The name of the runtime API to query.
            method: The specific method within the runtime API to call.
            params: The parameters to pass to the method call.
            block: the block number for this query. Do not specify if using
                block_hash or reuse_block
            block_hash: The hash of the blockchain block number at which to
                perform the query. Do not specify if using `block` or `reuse_block`.
            reuse_block: Whether to reuse the last-used block hash. Do not
                set if using `block_hash` or `block`.

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

    async def subnet_exists(
        self,
        netuid: int,
        block: int | None = None,
        block_hash: str | None = None,
        reuse_block: bool = False,
    ) -> bool:
        """
        Checks if a subnet with the specified unique identifier (netuid) exists within the Bittensor network.

        Arguments:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            block_hash (Optional[str]): The hash of the blockchain block number at which to check the subnet existence.
            reuse_block (bool): Whether to reuse the last-used block hash.

        Returns:
            `True` if the subnet exists, `False` otherwise.

        This function is critical for verifying the presence of specific subnets in the network,
        enabling a deeper understanding of the network's structure and composition.
        """
        block_hash = await self.determine_block_hash(block, block_hash, reuse_block)
        result = await self.substrate.query( # type: ignore
            module="SubtensorModule",
            storage_function="NetworksAdded",
            params=[netuid],
            block_hash=block_hash,
            reuse_block_hash=reuse_block,
        )
        return getattr(result, "value", False)

    @asyncstdlib.lru_cache(maxsize=128)
    async def _get_block_hash(self, block_id: int) -> str:
        return await self.substrate.get_block_hash(block_id) # type: ignore

    async def __aenter__(self):
        try:
            await self.substrate.initialize()
            return self
        except TimeoutError:
            raise ConnectionError
        except (ConnectionRefusedError, ssl.SSLError):
            raise ConnectionError

    async def __aexit__(
        self,
        cls: type[BaseException],
        exc: BaseException,
        tb: TracebackType
    ):
        await self.substrate.close()