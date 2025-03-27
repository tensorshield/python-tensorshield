from scalecodec.utils.ss58 import ss58_encode
from libtensorshield.types import Balance


SS58_FORMAT = 42


def decode_account_id(account_id_bytes: bytes | str | tuple[tuple[int, ...]]) -> str:
    """
    Decodes an AccountId from bytes to a Base64 string using SS58 encoding.

    Args:
        account_id_bytes (bytes): The AccountId in bytes that needs to be decoded.

    Returns:
        str: The decoded AccountId as a Base64 string.
    """
    if isinstance(account_id_bytes, tuple):
        account_id_bytes = bytes(account_id_bytes[0])

    if isinstance(account_id_bytes, str):
        account_id_bytes = str.encode(account_id_bytes)

    # Convert the AccountId bytes to a Base64 string
    return ss58_encode(bytes(account_id_bytes).hex(), SS58_FORMAT)


def process_stake_data(stake_data: list[tuple[bytes, int]]) -> dict[str, Balance]:
    """
    Processes stake data to decode account IDs and convert stakes from rao to Balance objects.

    Args:
        stake_data (list): A list of tuples where each tuple contains an account ID in bytes and a stake in rao.

    Returns:
        dict: A dictionary with account IDs as keys and their corresponding Balance objects as values.
    """
    decoded_stake_data: dict[str, Balance] = {}
    for account_id_bytes, stake_ in stake_data:
        account_id = decode_account_id(account_id_bytes)
        decoded_stake_data.update({account_id: Balance.from_rao(stake_)})
    return decoded_stake_data