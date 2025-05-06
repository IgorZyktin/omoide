"""General worker class for all workers."""

import asyncio
from collections.abc import Callable
import functools
import os
import signal

from omoide import custom_logging
from omoide.database.interfaces import AbsDatabase
from omoide.database.interfaces.abs_worker_repo import AbsWorkersRepo

LOG = custom_logging.get_logger(__name__)


class Worker:
    """General worker class for all workers."""

    def __init__(
        self,
        database: AbsDatabase,
        workers: AbsWorkersRepo,
        name: str,
        loop_callable: Callable,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.workers = workers
        self.name = name
        self.loop_callable = loop_callable
        self.stopping = False

    async def start(self, register: bool = True) -> None:
        """Start worker."""
        await self.register_signals()
        await self.database.connect()

        if register:
            async with self.database.transaction() as conn:
                await self.workers.register_worker(
                    conn=conn,
                    worker_name=self.name,
                )

        LOG.warning('Worker {!r} started', self.name)

    async def stop(self) -> None:
        """Start worker."""
        await self.database.disconnect()
        LOG.warning('Worker {!r} stopped', self.name)

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
            self.stopping = True

        loop.add_signal_handler(
            signal.SIGINT,
            functools.partial(signal_handler, sig=signal.SIGINT),
        )

        loop.add_signal_handler(
            signal.SIGTERM,
            functools.partial(signal_handler, sig=signal.SIGTERM),
        )

    async def run(self, short_delay: float, long_delay: float) -> None:
        """Daemon run."""
        try:
            while True:
                did_something = await self.execute()

                if self.stopping:
                    break

                if did_something:
                    await asyncio.sleep(short_delay)
                else:
                    await asyncio.sleep(long_delay)
        except (KeyboardInterrupt, asyncio.CancelledError):
            LOG.warning('Worker {!r} stopping', self.name)

    async def execute(self) -> bool:
        """Perform workload."""
        return await self.loop_callable()  # type: ignore [no-any-return]
