"""Worker that performs operations one by one."""

import time

import click
import ujson

from omoide import custom_logging
from omoide import serial_operations as so
from omoide import utils
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import cfg
from omoide.workers.serial import operations as op
from omoide.workers.serial.worker import SerialWorker

LOG = custom_logging.get_logger(__name__)


@click.command()
@click.option(
    '--operation',
    type=str,
    default='',
    help='Run this operation and then stop',
    show_default=True,
)
@click.option(
    '--extras',
    type=str,
    default='',
    help='JSON formatted extra parameters',
    show_default=True,
)
def main(operation: str, extras: str) -> None:
    """Entry point."""
    config = cfg.Config()
    mediator = WorkerMediator(
        database=sa.SqlalchemyDatabase(config.db_admin_url.get_secret_value()),
        items=sa.ItemsRepo(),
        tags=sa.TagsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
    )
    worker = SerialWorker(config, mediator)

    if operation:
        run_manual(worker, operation, extras)
    else:
        run_automatic(worker)


def run_manual(worker: SerialWorker, operation_name: str, extras: str) -> None:
    """Oneshot run."""
    worker.start(register=False)

    extras_dict = ujson.loads(extras) if extras else {}
    now = utils.now()
    kwargs = {
        'id': -1,
        'worker_name': 'manual',
        'status': so.OperationStatus.CREATED,
        'extras': extras_dict,
        'created_at': now,
        'updated_at': now,
        'started_at': now,
        'ended_at': None,
        'log': None,
    }

    LOG.info(
        'Running {!r} manually with extras {!r}',
        operation_name,
        extras_dict,
    )

    try:
        operation = so.SerialOperation.from_name(name=operation_name, **kwargs)
        executor = op.SerialOperationExecutor.from_operation(
            operation=operation,
            config=worker.config,
            mediator=worker.mediator,
        )
        executor.execute()
    finally:
        worker.stop()


def run_automatic(worker: SerialWorker) -> None:
    """Daemon run."""
    worker.start()

    try:
        while True:
            did_something = worker.execute()

            if worker.mediator.stopping:
                break

            if did_something:
                time.sleep(worker.config.short_delay)
            else:
                time.sleep(worker.config.long_delay)
    except KeyboardInterrupt:
        LOG.warning('Stopped manually')
    finally:
        worker.stop()


if __name__ == '__main__':
    main()
