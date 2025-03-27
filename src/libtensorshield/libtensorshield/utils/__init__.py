

__all__: list[str] = [
    'u16_normalized_float'
]

RAOPERTAO = 1e9

U16_MAX = 65535

U64_MAX = 18446744073709551615


def u16_normalized_float(x: int) -> float:
    return float(x) / float(U16_MAX)