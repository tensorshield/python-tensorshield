import asyncio
import inspect
import logging
import threading
from contextlib import AsyncExitStack
from typing import overload
from typing import Any
from typing import AsyncGenerator
from typing import Awaitable
from typing import Callable
from typing import ParamSpec
from typing import TypeAlias
from typing import TypeVar
from typing import TYPE_CHECKING

import fastapi
import fastapi.params
from fastapi.dependencies.utils import get_dependant
from fastapi.dependencies.utils import solve_dependencies

from tensorshield.ext.axon import SynapseResponse
from tensorshield.ext.protocol import Synapse
from tensorshield.ext.protocol import SynapseEnvelope
from ._task import Task
if TYPE_CHECKING:
    from ._soma import SynapseHandlerType
    from ._soma import Soma


P = ParamSpec('P')
R = TypeVar('R')
S = TypeVar('S', bound=Synapse)
SynapseHandlerMapping: TypeAlias = dict[str, 'SynapseHandlerType']


class TaskRunner:
    handlers: SynapseHandlerMapping
    logger: logging.Logger = logging.getLogger(__name__)
    running: set[asyncio.Task[None]]
    tasks: dict[str, Task[Any]]

    @overload
    async def run_handler(
        self,
        task: Task[Any],
        handler: Callable[P, AsyncGenerator[None | SynapseResponse, Synapse | None]]
    ) -> AsyncGenerator[None | SynapseResponse, Synapse | None]:
        ...

    @overload
    async def run_handler(
        self,
        task: Task[Any],
        handler: Callable[P, Awaitable[None | SynapseResponse]],
        envelope: SynapseEnvelope[Any]
    ) -> None | SynapseResponse:
        ...

    @property
    def pending(self) -> list[Task[Any]]:
        return [t for t in self.tasks.values() if t.is_runnable()]

    def __init__(
        self,
        soma: 'Soma[Any]',
        handlers: SynapseHandlerMapping,
        loop: asyncio.AbstractEventLoop
    ):
        self.handlers = handlers
        self.lock = threading.Lock()
        self.loop = loop
        self.running = set()
        self.soma = soma
        self.tasks = {}

    def get_handler(self, synapse: Synapse) -> 'SynapseHandlerType':
        return self.handlers[type(synapse).__name__]

    def schedule(
        self,
        envelope: SynapseEnvelope[S],
        future: asyncio.Future[SynapseResponse]
    ) -> None:
        k = self.soma.generate_task_id(envelope.synapse)
        with self.lock:
            task: Task[Any] | None = self.tasks.get(k)
            if task is None:
                self.logger.debug(
                    "Received new task (id: %s, kind: %s)",
                    k[:6],
                    type(envelope.synapse).__name__
                )
                task = Task(
                    task_id=k,
                    runner=self,
                    handler=self.get_handler(envelope.synapse)
                )
                self.tasks[k] = task
            else:
                self.logger.debug(
                    "Subscribing to existing task (id: %s, envelope: %s)",
                    k[:6],
                    type(envelope.synapse).__name__
                )
            task.subscribe(envelope, future)

    async def run_all(self) -> None:
        pending = self.pending

        self.logger.debug("Running %s pending tasks", len(pending))
        for task in pending:
            self.logger.debug(
                "Scheduled task (id: %s)",
                task.task_id[:6]
            )
            self.running.add(self.loop.create_task(task.run()))
        if not self.running:
            return
        self.logger.debug("Running tasks: %s", len(self.running))
        done, self.running = await asyncio.wait(self.running, timeout=0.1)
        self.logger.debug("Completed %s tasks", len(done))

    async def run_handler(
        self,
        task: Task[Any],
        handler: Callable[P, R],
        envelope: SynapseEnvelope[Any] | None = None,
        request: fastapi.Request | None = None
    ) -> Any:
        async with AsyncExitStack() as stack:
            cache:  dict[tuple[Callable[..., Any], tuple[str]], Any] = {}
            dependant, kwargs = await self.inject_dependencies(
                stack=stack,
                task=task,
                handler=handler,
                envelope=envelope,
                request=request,
                cache=cache
            )
            assert dependant.call is not None
            assert callable(dependant.call)
            result = dependant.call(**kwargs)
            if inspect.isawaitable(result):
                result = await result
            return result

    async def inject_dependencies(
        self,
        stack: AsyncExitStack,
        task: Task[Any],
        handler: Callable[..., Any],
        envelope: SynapseEnvelope[S] | None,
        cache: dict[tuple[Callable[..., Any], tuple[str]], Any],
        request: fastapi.Request | None = None
    ):
        body = None
        path = '/'
        if envelope is not None:
            body = envelope.synapse.model_dump(mode='json')
            path = f'/{type(envelope.synapse).__name__}'
        request = self.request_factory(request, path, envelope)

        # Add the task to the request state so that it
        # can be injected later.
        request.state.task = task

        dependant = get_dependant(call=handler, path=path)
        values, errors, *_ = await solve_dependencies(
            request=request,
            dependant=dependant,
            body=body,
            dependency_overrides_provider=None,
            dependency_cache=cache,
            async_exit_stack=stack
        )
        if errors:
            raise ValueError(errors)
        cache.update(cache)
        assert dependant.call is not None
        assert callable(dependant.call)
        return dependant, values

    def request_factory(
        self,
        request: fastapi.Request | None,
        path: str,
        envelope: SynapseEnvelope[Any] | None = None
    ) -> fastapi.Request:
        if request is None:
            scope: dict[str, Any] = {
                'type': 'http',
                'path': path,
                'query_string': '',
                'headers': []
            }
            if envelope is not None:
                scope['client'] = (envelope.remote_host, envelope.remote_port)
            request = fastapi.Request(scope=scope)
        return request