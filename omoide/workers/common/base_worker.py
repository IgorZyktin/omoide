"""General worker class for all workers."""

import abc
import asyncio
import functools
import os
import signal
from typing import Generic
from typing import TypeVar

from omoide import custom_logging

LOG = custom_logging.get_logger(__name__)

ConfigT = TypeVar('ConfigT')
DbT = TypeVar('DbT')


class BaseWorker(Generic[ConfigT, DbT], abc.ABC):
    """General worker class for all workers."""

    def __init__(self, config: ConfigT, db: DbT) -> None:
        """Initialize instance."""
        self.config = config
        self.db = db
        self.stopping = False

    async def start(self) -> None:
        """Start worker."""
        await self.db.connect()
        await self.db.register_worker()
        LOG.info('Worker {} started', self.config.name)

    async def stop(self) -> None:
        """Start worker."""
        await self.db.disconnect()
        LOG.info('Worker {} stopped', self.config.name)

    def register_signals(self, loop: asyncio.AbstractEventLoop) -> None:
        """Decide how we will stop."""
        if os.name == 'nt':
            LOG.warning('Running on Windows, can stop only using Ctr+C')
            return

        def signal_handler(sig: int) -> None:
            """Handle signal."""
            string = signal.strsignal(sig)
            LOG.info('Caught signal {}, stopping', string)
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
