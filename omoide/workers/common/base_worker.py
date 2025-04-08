"""General worker class for all workers."""

import abc
import asyncio
import functools
import os
import signal

from omoide import custom_logging
from omoide.workers.common.mediator import WorkerMediator

LOG = custom_logging.get_logger(__name__)


class BaseWorker(abc.ABC):
    """General worker class for all workers."""

    def __init__(self, mediator: WorkerMediator, name: str) -> None:
        """Initialize instance."""
        self.mediator = mediator
        self.name = name
        self.stopping = False

    async def start(self, register: bool = True) -> None:
        """Start worker."""
        await self.register_signals()
        await self.mediator.database.connect()

        if register:
            async with self.mediator.database.transaction() as conn:
                await self.mediator.workers.register_worker(
                    conn=conn,
                    worker_name=self.name,
                )

        LOG.info('Worker {!r} started', self.name)

    async def stop(self) -> None:
        """Start worker."""
        await self.mediator.database.disconnect()
        LOG.info('Worker {!r} stopped', self.name)

    async def register_signals(self) -> None:
        """Decide how we will stop."""
        if os.name == 'nt':
            LOG.warning('Running on Windows, can stop only using Ctr+C')
            return

        loop = asyncio.get_event_loop()

        def signal_handler(sig: int) -> None:
            """Handle signal."""
            string = signal.strsignal(sig)
            LOG.info('Worker {!r} caught signal {}, stopping', self.name, string)
            loop.remove_signal_handler(sig)
            self.mediator.stopping = True

        loop.add_signal_handler(
            signal.SIGINT,
            functools.partial(signal_handler, sig=signal.SIGINT),
        )

        loop.add_signal_handler(
            signal.SIGTERM,
            functools.partial(signal_handler, sig=signal.SIGTERM),
        )

    @abc.abstractmethod
    async def execute(self) -> bool:
        """Perform workload."""
