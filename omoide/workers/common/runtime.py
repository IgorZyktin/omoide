"""Common runtime utilities."""

import asyncio

from omoide import custom_logging
from omoide.workers.common.base_worker import BaseWorker

LOG = custom_logging.get_logger(__name__)


async def run_automatic(worker: BaseWorker, short_delay: float, long_delay: float) -> None:
    """Daemon run."""
    await worker.start()

    try:
        while True:
            did_something = await worker.execute()

            if worker.stopping:
                break

            if did_something:
                await asyncio.sleep(short_delay)
            else:
                await asyncio.sleep(long_delay)
    except (KeyboardInterrupt, asyncio.CancelledError):
        LOG.warning('Worker {!r} is requested to stop manually', worker.name)
    finally:
        await worker.stop()
