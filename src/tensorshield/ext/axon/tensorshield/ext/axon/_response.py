import fastapi

from tensorshield.ext.protocol import Synapse


class SynapseResponse(fastapi.responses.JSONResponse):

    def __init__(
        self,
        synapse: Synapse,
        status_code: int = 200
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
        self.headers.update(synapse.to_headers()) # type: ignore
        self.headers['Content-Type'] = "application/json"