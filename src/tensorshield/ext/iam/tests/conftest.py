from typing import Any

import fastapi
import httpx
import pytest
import pytest_asyncio
from tensorshield.ext.wallet.testing import TEST_KEYS

from tensorshield.ext.iam.credentials import HTTPHotkeySigned
from tensorshield.ext.iam.models import HTTPHotkeySignedHeaders


BASE_URL = base_url="http://testserver"

CLIENT_KEY = TEST_KEYS.items['miner-a/1']

SERVER_KEY = TEST_KEYS.items['validator-a/1']


@pytest.fixture
def auth():
    return HTTPHotkeySigned(CLIENT_KEY)


@pytest_asyncio.fixture
async def client(transport: httpx.ASGITransport, auth: httpx.Auth):
    async with httpx.AsyncClient(transport=transport, auth=auth, base_url=BASE_URL) as c:
        yield c

@pytest.fixture
def transport():
    return httpx.ASGITransport(app)


app = fastapi.FastAPI()


@app.post('/')
async def home(request: fastapi.Request):
    headers = HTTPHotkeySignedHeaders.model_validate_request(request)
    opts: dict[str, Any] = {}
    if await request.body():
        opts = await request.json()
    response = fastapi.responses.JSONResponse(
        content={
            'headers': headers.model_dump(mode='json'),
            'verified': headers.verify(await request.body())
        }
    )
    if not opts.get('skip_response_signature'):
        if headers.audience == SERVER_KEY.ss58_address:
            response.headers['X-Bittensor-Signature'] = headers.sign_response(SERVER_KEY, response.body)
        if opts.get('invalidate_signature'):
            response.headers['X-Bittensor-Signature'] = headers.sign_response(SERVER_KEY, b'')
        if opts.get('nonhex_signature'):
            response.headers['X-Bittensor-Signature'] = 'abc'
        if opts.get('malformed_signature'):
            response.headers['X-Bittensor-Signature'] = response.headers['X-Bittensor-Signature'][:-1]
    return response