"""General worker class for all workers."""

import abc
import asyncio
import functools
import os
import signal
from typing import Generic
from typing import TypeVar

from omoide import custom_logging
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.database.interfaces.abs_worker_repo import AbsWorkerRepo

LOG = custom_logging.get_logger(__name__)

ConfigT = TypeVar('ConfigT')


class BaseWorker(Generic[ConfigT], abc.ABC):
    """General worker class for all workers."""

    def __init__(
        self,
        config: ConfigT,
        database: AbsDatabase,
        repo: AbsWorkerRepo,
    ) -> None:
        """Initialize instance."""
        self.config = config
        self.database = database
        self.repo = repo
        self.stopping = False

    async def start(self, worker_name: str) -> None:
        """Start worker."""
        await self.database.connect()

        async with self.database.transaction() as conn:
            await self.repo.register_worker(conn, worker_name)

        LOG.info('Worker {} started', worker_name)

    async def stop(self, worker_name: str) -> None:
        """Start worker."""
        await self.database.disconnect()
        LOG.info('Worker {} stopped', worker_name)

    def register_signals(self, loop: asyncio.AbstractEventLoop) -> None:
        """Decide how we will stop."""
        if os.name == 'nt':
            LOG.warning('Running on Windows, can stop only using Ctr+C')
            return

        def signal_handler(sig: int) -> None:
            """Handle signal."""
            string = signal.strsignal(sig)
            LOG.info('Worker caught signal {}, stopping', string)
            loop.remove_signal_handler(sig)
            self.stopping = True

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
