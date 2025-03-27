import operator

import pytest

from libtensorshield.types import Balance


@pytest.mark.parametrize("a,b", [
    (1, 1),
    (1.0, 1.0),
    (Balance(1.0), Balance(1.0))
])
def test_eq(a: int | float | Balance, b: int | float | Balance):
    assert Balance(a) == Balance(b)


def test_eq_int():
    assert Balance(1) == 1


def test_ne():
    assert Balance(1) != Balance(2)


def test_gt():
    assert Balance(2) > Balance(1)
    assert Balance(2) > 1.0


def test_lt():
    assert Balance(1) < Balance(2)
    assert Balance(1.0) < Balance(2.0)
    assert Balance(1) < 2

def test_ge():
    assert operator.ge(Balance(1), Balance(1))
    assert operator.ge(Balance(2), Balance(1))
    assert not operator.ge(Balance(1), Balance(2))

def test_le():
    assert operator.le(Balance(1), Balance(1))
    assert operator.le(Balance(1), Balance(2))
    assert not operator.le(Balance(2), Balance(1))


def test_add():
    assert Balance(1) + Balance(1) == Balance(2)
    assert Balance(1.0) + Balance(1.0) == Balance(2.0)
    assert Balance(1) + 1 == Balance(2)


def test_radd():
    assert 1 + Balance(1) == Balance(2)


def test_mul():
    assert Balance(1) * Balance(2) == Balance(2)
    #assert Balance(1.0) * Balance(2.0) == Balance(2.0)
    assert Balance(1) * 2 == Balance(2)
    assert Balance(1.0) * 0.5 == Balance(0.5)


def test_rmul():
    assert 1 * Balance(2) == Balance(2)


def test_sub():
    assert Balance(1) - Balance(1) == Balance(0)
    assert Balance(1.0) - Balance(1.0) == Balance(0)
    assert Balance(1) - 1 == Balance(0)


def test_rsub():
    assert 1 - Balance(1) == Balance(0)


def test_div():
    assert Balance(4) / Balance(2) == Balance(2)
    assert Balance(4.0) / 2 == Balance(2.0)
    assert Balance(4.0) * 0.5 == Balance(2.0)


def test_bool():
    assert bool(Balance(1)) is True
    assert not bool(Balance(0)) is False


def test_abs():
    assert abs(Balance(-1)) == Balance(1)


def test_neg():
    assert -(Balance(1)) == Balance(-1)


def test_rdiv():
    assert 4 / Balance(2) == Balance(2)


def test_eq_none():
    assert not Balance(1) == None


def test_as_tao():
    assert Balance(1000000000).tao == 1


def test_cast_int():
    assert int(Balance(1.0)) == 1000000000


def test_cast_float():
    assert float(Balance(1.0)) == 1.0


def test_from_float():
    assert Balance.from_float(1.0) == Balance(1.0)


def test_from_tao():
    assert Balance.from_tao(1.0) == Balance(1.0)