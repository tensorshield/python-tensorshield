import httpx
import pytest

from tensorshield.ext.iam.types import InvalidSignature
from tensorshield.ext.iam.types import MissingSignature
from ..conftest import SERVER_KEY


@pytest.mark.asyncio
async def test_simple_request(client: httpx.AsyncClient):
    response = await client.post('/')
    assert response.status_code == 200
    dto = response.json()
    assert dto['verified'], dto


@pytest.mark.asyncio
async def test_simple_request_with_body(client: httpx.AsyncClient):
    response = await client.post('/', json={'foo': 'bar'})
    assert response.status_code == 200
    dto = response.json()
    assert dto['verified'], dto


@pytest.mark.asyncio
async def test_simple_require_receiver_signature(client: httpx.AsyncClient):
    response = await client.post(
        url='/',
        headers={
            'X-Bittensor-Audience': SERVER_KEY.ss58_address
        }
    )
    assert response.status_code == 200
    dto = response.json()
    assert dto['verified'], dto


@pytest.mark.asyncio
async def test_network_require_receiver_signature(client: httpx.AsyncClient):
    response = await client.post(
        url='/',
        headers={
            'X-Bittensor-Audience': SERVER_KEY.ss58_address,
            'X-Bittensor-Network': 'finney',
            'X-Bittensor-Subnet-ID': '0',
        }
    )
    assert response.status_code == 200
    dto = response.json()
    assert dto['verified'], dto


@pytest.mark.asyncio
async def test_missing_signature_raises(client: httpx.AsyncClient):
    with pytest.raises(MissingSignature):
        await client.post(
            url='/',
            json={'skip_response_signature': True},
            headers={
                'X-Bittensor-Audience': SERVER_KEY.ss58_address
            }
        )


@pytest.mark.asyncio
async def test_invalid_signature_raises(client: httpx.AsyncClient):
    with pytest.raises(InvalidSignature):
        await client.post(
            url='/',
            json={'invalidate_signature': True},
            headers={
                'X-Bittensor-Audience': SERVER_KEY.ss58_address
            }
        )


@pytest.mark.asyncio
async def test_nonhex_signature_raises(client: httpx.AsyncClient):
    with pytest.raises(InvalidSignature):
        await client.post(
            url='/',
            json={'nonhex_signature': True},
            headers={
                'X-Bittensor-Audience': SERVER_KEY.ss58_address
            }
        )


@pytest.mark.asyncio
async def test_malformed_signature_raises(client: httpx.AsyncClient):
    with pytest.raises(InvalidSignature):
        await client.post(
            url='/',
            json={'malformed_signature': True},
            headers={
                'X-Bittensor-Audience': SERVER_KEY.ss58_address
            }
        )
