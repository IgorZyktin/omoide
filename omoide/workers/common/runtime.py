"""Common runtime utilities."""

import asyncio

from omoide import custom_logging
from omoide.workers.parallel.worker import ParallelWorker
from omoide.workers.serial.worker import SerialWorker

LOG = custom_logging.get_logger(__name__)


async def run_automatic(worker: SerialWorker | ParallelWorker) -> None:
    """Daemon run."""
    await worker.start()

    try:
        while True:
            did_something = await worker.execute()

            if worker.mediator.stopping:
                break

            if did_something:
                await asyncio.sleep(worker.config.short_delay)
            else:
                await asyncio.sleep(worker.config.long_delay)
    except (KeyboardInterrupt, asyncio.CancelledError):
        LOG.warning('Worker {!r} stopped manually', worker.config.name)
    finally:
        await worker.stop()
