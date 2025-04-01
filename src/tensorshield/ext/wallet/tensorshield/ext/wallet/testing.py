from libtensorshield.testing import WALLET_PATH

from .models import HotkeySet


TEST_KEYS = HotkeySet()
TEST_KEYS.add('miner-a', '1')
TEST_KEYS.add('miner-a', '2')
TEST_KEYS.add('miner-b', '1')
TEST_KEYS.add('miner-b', '2')
TEST_KEYS.add('validator-a', '1')
TEST_KEYS.add('validator-a', '2')
TEST_KEYS.add('validator-b', '1')
TEST_KEYS.add('validator-b', '2')
TEST_KEYS.load(WALLET_PATH, mode='private')