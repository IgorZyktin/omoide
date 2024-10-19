"""Worker that performs operations one by one."""

import asyncio

from omoide import custom_logging
from omoide.database.implementations.impl_sqlalchemy.database import (
    SqlalchemyDatabase,
)
from omoide.database.implementations.impl_sqlalchemy.worker_repo import (
    WorkerRepo,
)
from omoide.database.implementations.impl_sqlalchemy.users_repo import (
    UsersRepo,
)
from omoide.workers.serial import cfg
from omoide.workers.serial.worker import SerialWorker

LOG = custom_logging.get_logger(__name__)


async def main() -> None:
    """Entry point."""
    config = cfg.Config()
    database = SqlalchemyDatabase(config.db_admin_url.get_secret_value())
    worker_repo = WorkerRepo()
    users_repo = UsersRepo()
    worker = SerialWorker(config, database, worker_repo, users_repo)

    await worker.start(config.name)
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
        await worker.stop(config.name)


if __name__ == '__main__':
    asyncio.run(main())
