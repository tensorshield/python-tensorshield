from typing import TypedDict


class FixedPoint(TypedDict):
    """
    Represents a fixed point ``U64F64`` number.
    Where ``bits`` is a U128 representation of the fixed point number.

    This matches the type of the Alpha shares.
    """

    bits: int