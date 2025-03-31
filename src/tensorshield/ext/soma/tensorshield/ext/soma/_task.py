import asyncio
import inspect
import logging
import time
from typing import Any
from typing import Generic
from typing import TypeVar
from typing import Union
from typing import TYPE_CHECKING

import fastapi

from tensorshield.ext.axon import SynapseResponse
from tensorshield.ext.protocol import Synapse
from tensorshield.ext.protocol import SynapseEnvelope
if TYPE_CHECKING:
    from ._soma import SynapseTask
    from ._soma import SynapseHandlerType
    from ._taskrunner import TaskRunner


T = TypeVar('T', bound=Synapse)


class Task(Generic[T]):
    handler: Union['SynapseHandlerType', 'SynapseTask']
    logger: logging.Logger = logging.getLogger(__name__)
    task_id: str
    subscribers: list[tuple[SynapseEnvelope[T], asyncio.Future[Any]]]

    def __init__(
        self,
        runner: 'TaskRunner',
        handler: 'SynapseHandlerType',
        task_id: str
    ):
        self.task_id = task_id
        self.created = time.time()
        self.handler = handler
        self.subscribers = []
        self.running = False
        self.runner = runner
        self.processed = 0
        self._lock = asyncio.Lock()

    def is_initial(self) -> bool:
        return self.processed == 0

    def is_runnable(self):
        return any([
            bool(self.subscribers) and not self.running,
        ])

    def lock(self):
        return self._lock

    def subscribe(
        self,
        envelope: SynapseEnvelope[T],
        future: asyncio.Future[SynapseResponse]
    ):
        self.logger.debug(
            "Creating subscription for %s (task-id: %s)",
            type(envelope.synapse).__name__,
            self.task_id[:6]
        )
        self.subscribers.append((envelope, future))

    async def age(self, min_age: int):
        """Block until the task has reached the given age, in seconds."""
        td = time.time() - self.created
        await asyncio.sleep(max(0, min_age - td))

    async def run(self) -> None:
        """Runs all subscribing synapses sequentially."""
        async with self.lock():
            self.logger.debug(
                "Running handler on all synapses (task-id: %s)",
                self.task_id[:6]
            )
            try:
                self.running = True
                await self._run()
            except Exception as e:
                self.logger.exception(
                    "Caught fatal %s while running handler: %s",
                    type(e).__name__,
                    repr(e)
                )
            finally:
                self.logger.debug(
                    "Finished running (task-id: %s, total: %s)",
                    self.task_id[:6],
                    self.processed
                )
                self.running = False

    async def _run(self):
        if inspect.isasyncgenfunction(self.handler):
            self.handler = await self.runner.run_handler(task=self, handler=self.handler)
            assert inspect.isasyncgen(self.handler)
            await self.handler.asend(None)
        while True:
            try:
                envelope, future = self.subscribers.pop()
            except IndexError:
                break
            try:
                if inspect.isasyncgen(self.handler):
                    result = await self.handler.asend(envelope.synapse)
                else:
                    result = await self.runner.run_handler(
                        self,
                        self.handler, # type: ignore
                        envelope=envelope
                    )
            except StopAsyncIteration:
                # Assume here that a fatal exception occurred earlier within the loop.
                result = SynapseResponse(
                    synapse=envelope.synapse,
                    status_code=500
                )
            except Exception as e:
                self.logger.exception(
                    'Caught fatal %s while running handler: %s',
                    type(e).__name__,
                    repr(e)
                )
                result = SynapseResponse(
                    synapse=envelope.synapse,
                    status_code=500
                )
            self.processed += 1
            if not isinstance(result, (Synapse, fastapi.Response)):
                raise TypeError(
                    f"Handler for {type(envelope.synapse).__name__} did not return "
                    f"a bittensor.Synapse or fastapi.Response object: {repr(result)}."
                )
            if isinstance(result, Synapse):
                result = SynapseResponse(synapse=result)
            self.runner.loop.call_soon_threadsafe(future.set_result, result)
        assert not self.subscribers

    def __await__(self):
        return self.run().__await__()