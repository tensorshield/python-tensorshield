from typing import TypeVar

import httpx

from ._requestmodel import RequestModel
from ._responsemodel import ResponseModel


R = TypeVar('R', bound=ResponseModel)


class HTTPClient(httpx.AsyncClient):

    async def submit(self, request: RequestModel[R]) -> R:
        response = await self.request(
            method=request.method,
            url=request.qualpath(),
            json=request.model_dump(mode='json')
        )
        if response.is_success:
            response.raise_for_status() # TODO
        return request.response_model.model_validate_json(response.text)