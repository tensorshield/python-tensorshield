import asyncio
import logging
import time

import fastapi

from tensorshield.ext.protocol import Synapse


logger: logging.Logger = logging.getLogger(__name__)


class SynapseResponse(fastapi.responses.JSONResponse):
    delay: float = 0.0
    synapse: Synapse

    def __init__(
        self,
        synapse: Synapse,
        status_code: int = 200,
        delay: float = 0.0
    ):
        if synapse.axon is not None:
            synapse.axon.status_code = status_code
            synapse.axon.status_message = "Success"
            if status_code >= 400:
                synapse.axon.status_message = "Error"
        super().__init__(
            status_code=status_code,
            content=synapse.model_dump(mode='json')
        )
        self.delay = delay
        self.headers.update(synapse.to_headers()) # type: ignore
        self.headers['Content-Type'] = "application/json"
        self.synapse = synapse

    def is_delayed(self):
        return self.delay > 0.0

    async def hold(self, received: float, assumed_latency: float = 1.0):
        """Block with the given `delay`, ensuring not to exceed the synapse
        timeout.
        """
        assert self.synapse.axon
        assert self.synapse.dendrite
        timeout = (self.synapse.timeout or 0.0)
        elapsed = time.monotonic() - received - assumed_latency
        remaining = max(timeout - elapsed, 0.0)
        delay = min(self.delay, remaining)

        logger.info(
            "Withholding %s for %.02fs (sender: %s, receiver: %s, elapsed: %.02f)",
            type(self.synapse).__name__,
            delay,
            self.synapse.dendrite.hotkey,
            self.synapse.axon.hotkey,
            elapsed
        )
        await asyncio.sleep(delay)
