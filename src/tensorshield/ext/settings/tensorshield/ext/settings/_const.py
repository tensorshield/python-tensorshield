import os


__all__: list[str] = [
    'get_chain_endpoint',
    'get_network',
    'DEFAULT_NETWORK'
]


DEFAULT_NETWORK: str = 'finney'

NETWORKS = ["finney", "test", "archive", "local", "subvortex", "rao", "latent-lite"]

FINNEY_ENTRYPOINT: str = "wss://entrypoint-finney.opentensor.ai:443"

FINNEY_TEST_ENTRYPOINT: str = "wss://test.finney.opentensor.ai:443"

ARCHIVE_ENTRYPOINT: str = "wss://archive.chain.opentensor.ai:443"

LOCAL_ENTRYPOINT: str = os.getenv("BT_SUBTENSOR_CHAIN_ENDPOINT") or "ws://127.0.0.1:9944"

SUBVORTEX_ENTRYPOINT: str = "ws://subvortex.info:9944"

RAO_ENTRYPOINT: str = "wss://rao.chain.opentensor.ai:443"

LATENT_LITE_ENTRYPOINT: str = "wss://lite.sub.latent.to:443"

NETWORK_CHAIN_ENDPOINTS = {
    NETWORKS[0]: FINNEY_ENTRYPOINT,
    NETWORKS[1]: FINNEY_TEST_ENTRYPOINT,
    NETWORKS[2]: ARCHIVE_ENTRYPOINT,
    NETWORKS[3]: LOCAL_ENTRYPOINT,
    NETWORKS[4]: SUBVORTEX_ENTRYPOINT,
    NETWORKS[5]: RAO_ENTRYPOINT,
    NETWORKS[6]: LATENT_LITE_ENTRYPOINT,
}

CHAIN_ENDPOINT_NETWORKS = {
    FINNEY_ENTRYPOINT: NETWORKS[0],
    FINNEY_TEST_ENTRYPOINT: NETWORKS[1],
    ARCHIVE_ENTRYPOINT: NETWORKS[2],
    LOCAL_ENTRYPOINT: NETWORKS[3],
    SUBVORTEX_ENTRYPOINT: NETWORKS[4],
    RAO_ENTRYPOINT: NETWORKS[5],
    LATENT_LITE_ENTRYPOINT: NETWORKS[6],
}


def get_chain_endpoint(network: str) -> str:
    return NETWORK_CHAIN_ENDPOINTS[network]


def get_network(chain_endpoint: str) -> str | None:
    return CHAIN_ENDPOINT_NETWORKS.get(chain_endpoint)