"""Worker that performs operations one by one."""

import asyncio

from omoide import custom_logging
from omoide.workers.serial.cfg import get_config
from omoide.workers.serial.database import SerialDatabase
from omoide.workers.serial.worker import SerialWorker

LOG = custom_logging.get_logger(__name__)


async def main():
    """Entry point."""
    config = get_config()
    database = SerialDatabase(config)
    worker = SerialWorker(config, database)

    await worker.start()
    loop = asyncio.get_event_loop()
    worker.register_signals(loop)

    try:
        while True:
            did_something = await worker.execute()

            if worker.stopping:
                break

            if did_something:
                await asyncio.sleep(config.short_delay)
            else:
                await asyncio.sleep(config.long_delay)
    except (KeyboardInterrupt, asyncio.CancelledError):
        LOG.warning('Stopped manually')
    finally:
        await worker.stop()


if __name__ == '__main__':
    asyncio.run(main())
