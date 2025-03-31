from scalecodec.utils.ss58 import ss58_encode


__all__: list[str] = [
    'u16_normalized_float'
]

RAOPERTAO = 1e9

SS58_FORMAT = 42

U16_MAX = 65535

U64_MAX = 18446744073709551615


def u16_normalized_float(x: int) -> float:
    return float(x) / float(U16_MAX)


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