import os

import bittensor
from libtensorshield.types import SS58Address

from tensorshield.ext.wallet import Hotkey


def test_validate_signature():
    k = os.urandom(32)
    bk = bittensor.Keypair.create_from_seed(k) # type: ignore
    ck = SS58Address(bk.ss58_address) # type: ignore

    msg = 'Hello world!'
    sig: bytes = bk.sign(msg) # type: ignore

    assert bk.ss58_address == ck # type: ignore
    assert bk.verify(msg, sig) == ck.verify(msg, sig) # type: ignore


def test_validate_signature_hex():
    k = os.urandom(32)
    bk = bittensor.Keypair.create_from_seed(k) # type: ignore
    ck = SS58Address(bk.ss58_address) # type: ignore

    msg = 'Hello world!'
    sig: bytes = '0x' + bytes.hex(bk.sign(msg)) # type: ignore

    assert bk.ss58_address == ck # type: ignore
    assert bk.verify(msg, sig) == ck.verify(msg, sig) # type: ignore


def test_signature_is_equal():
    k1 = Hotkey.generate('test', '1')
    k2 = bittensor.Keypair(ss58_address=k1.ss58_address) # type: ignore
    m = b'Hello world!'
    sig1 = k1.sign(m)
    assert k1.ss58_address == k2.ss58_address # type: ignore
    assert k1.verify(m, sig1)
    assert k1.ss58_address.verify(m, '0x' + bytes(sig1).hex())
    assert k2.verify(m, sig1) # type: ignore