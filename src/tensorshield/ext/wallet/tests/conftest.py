import pathlib

import pytest

from tensorshield.ext.wallet.models import Hotkey


SRCDIR = pathlib.Path(__file__).parent.parent

ETCDIR = SRCDIR.joinpath('etc')

WALLETDIR = ETCDIR.joinpath('wallets')


@pytest.fixture(scope='session')
def hotkey() -> Hotkey:
    return Hotkey.model_validate({
        'name': 'testing1',
        'hotkey': '1'
    })


@pytest.fixture(scope='session')
def wallet_path() -> pathlib.Path:
    return WALLETDIR