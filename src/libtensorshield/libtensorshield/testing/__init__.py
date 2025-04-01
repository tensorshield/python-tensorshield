import pathlib


RESOURCE_DIR: pathlib.Path = pathlib.Path(__file__).parent.joinpath('resources')

WALLET_PATH: pathlib.Path = RESOURCE_DIR.joinpath('wallets')