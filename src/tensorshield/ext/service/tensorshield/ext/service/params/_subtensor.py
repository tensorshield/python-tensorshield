from typing import Annotated
from typing import TypeAlias

import fastapi
from tensorshield.ext.subtensor import AsyncSubtensor


async def get(request: fastapi.Request):
    if not request.app.subtensor:
        raise NotImplementedError(
            f"{type(request.app)} is not configured with a subtensor."
        )
    return request.app.subtensor


Subtensor: TypeAlias = Annotated[AsyncSubtensor, fastapi.Depends(get)]