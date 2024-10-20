"""Worker that performs operations one by one."""

import time

from omoide import custom_logging
from omoide.database.implementations.impl_sqlalchemy.database import (
    SqlalchemyDatabase,
)
from omoide.database.implementations.impl_sqlalchemy.users_repo import (
    UsersRepo,
)
from omoide.database.implementations.impl_sqlalchemy.worker_repo import (
    WorkersRepo,
)
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import cfg
from omoide.workers.serial.worker import SerialWorker

LOG = custom_logging.get_logger(__name__)


def main() -> None:
    """Entry point."""
    config = cfg.Config()
    mediator = WorkerMediator(
        database=SqlalchemyDatabase(config.db_admin_url.get_secret_value()),
        users=UsersRepo(),
        workers=WorkersRepo(),
    )
    worker = SerialWorker(config, mediator)

    worker.start()

    try:
        while True:
            did_something = worker.execute()

            if worker.stopping:
                break

            if did_something:
                time.sleep(config.short_delay)
            else:
                time.sleep(config.long_delay)
    except KeyboardInterrupt:
        LOG.warning('Stopped manually')
    finally:
        worker.stop()


if __name__ == '__main__':
    main()
