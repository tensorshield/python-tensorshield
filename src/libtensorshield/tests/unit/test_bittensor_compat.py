import os

import bittensor

from libtensorshield.types import SS58Address


def test_public_key_is_equal():
    k = os.urandom(32)
    bk = bittensor.Keypair.create_from_seed(k) # type: ignore
    ck = SS58Address(bk.ss58_address) # type: ignore
    assert ck.public_bytes == bk.public_key # type: ignore


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