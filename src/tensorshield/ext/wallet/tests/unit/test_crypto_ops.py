import pathlib

from tensorshield.ext.wallet.models import Hotkey
from tensorshield.ext.wallet.models import HotkeyRef
from tensorshield.ext.wallet.models import HotkeyPublicKey
from tensorshield.ext.wallet.models import HotkeyPrivateKey


def test_load_public(wallet_path: pathlib.Path, hotkey: Hotkey):
    assert isinstance(hotkey.root, HotkeyRef)
    hotkey.load(wallet_path, mode='public')
    assert isinstance(hotkey.root, HotkeyPublicKey)


def test_load_private(wallet_path: pathlib.Path, hotkey: Hotkey):
    assert isinstance(hotkey.root, HotkeyRef)
    hotkey.load(wallet_path, mode='private')
    assert isinstance(hotkey.root, HotkeyPrivateKey)


def test_parse_ss58_public_key(wallet_path: pathlib.Path, hotkey: Hotkey):
    hotkey.load(wallet_path, mode='public')
    assert hotkey.public_bytes == hotkey.ss58_address.public_bytes

