import logging
import time
import uuid
from typing import Any
from typing import Generic
from typing import NoReturn
from typing import TypeVar

import fastapi
import pydantic
from libcanonical.bases import StateLogger
from starlette.requests import empty_receive
from starlette.requests import empty_send
from starlette.types import Receive, Scope, Send

from tensorshield.ext.protocol import Synapse
from tensorshield.ext.protocol import SynapseEnvelope
from tensorshield.ext.protocol import SynapseHeader


BITTENSOR_VERSION: int = 9001000

S = TypeVar('S', bound=Synapse)


class SynapseRequest(fastapi.Request, StateLogger, Generic[S]):
    _synapse: S | None
    logger = logging.getLogger(__name__)
    model: type[S]

    @property
    def validator_hotkey(self):
        return self.header.dendrite_hotkey

    def __init__(
        self,
        model: type[S],
        scope: Scope,
        receive: Receive = empty_receive,
        send: Send = empty_send
    ):
        super().__init__(scope, receive, send)
        self.model = model
        self.header = SynapseHeader.model_validate_headers(self.headers)
        self._synapse = None

    @property
    def synapse(self) -> S:
        if self._synapse is None:
            assert self.client is not None
            try:
                synapse = self.model.from_headers(dict(self.headers)) # type: ignore
            except pydantic.ValidationError:
                self.fail(422)
            else:
                if not synapse.axon:
                    self.fail(400, "Synapse did not specify a valid axon.")
                if not synapse.dendrite:
                    self.fail(400, "Synapse did not specify a valid dendrite.")
                synapse.axon.__dict__.update({
                    "version": str(BITTENSOR_VERSION),
                    "uuid": str(uuid.uuid4()),
                    "nonce": time.time_ns(),
                    "status_code": 100,
                })
                synapse.dendrite.__dict__.update({
                    "port": str(self.client.port),
                    "ip": str(self.client.host)
                })
                self._synapse = synapse # type: ignore
        assert self._synapse is not None
        return self._synapse

    def fail(self, status_code: int, message: str | None = "The service refused the request.") -> NoReturn:
        raise fastapi.HTTPException(status_code=status_code, detail=message)

    def get_logging_parameters(self) -> dict[str, Any]:
        return {
            'version': BITTENSOR_VERSION
        }

    def verify(self):
        if not self.synapse.dendrite:
            self.fail(400, "Synapse does not specify a dendrite.")
        if not self.synapse.dendrite.signature:
            self.fail(403, "Synapses must be signed by the sender.")
        message = str.join('.', [
            str(self.synapse.dendrite.nonce),
            str(self.synapse.dendrite.hotkey),
            str(self.header.axon_hotkey),
            str(self.synapse.dendrite.uuid),
            str(self.synapse.computed_body_hash)
        ])
        return self.header.dendrite_hotkey.verify(message, self.synapse.dendrite.signature)

    async def envelope(self) -> SynapseEnvelope[S]:
        assert self.client is not None
        return SynapseEnvelope(
            remote_host=self.client.host,
            remote_port=self.client.port,
            headers=self.header,
            synapse=self.model.model_validate_json(await self.body())
        )