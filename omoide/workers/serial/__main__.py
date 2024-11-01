"""Worker that performs operations one by one."""

import asyncio
from typing import Annotated

import typer
import ujson

from omoide import custom_logging
from omoide import serial_operations as so
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import cfg
from omoide.workers.serial import operations as op
from omoide.workers.serial.worker import SerialWorker

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


@app.command()
def main(
    operation: Annotated[str, typer.Option(help='Run this operation and then stop')] = '',
    extras: Annotated[str, typer.Option(help='JSON formatted extra parameters')] = '',
) -> None:
    """Entry point."""
    asyncio.run(_main(operation, extras))


async def _main(operation: str, extras: str) -> None:
    """ASync entry point."""
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
        await run_manual(worker, operation, extras)
    else:
        await run_automatic(worker)


async def run_manual(
    worker: SerialWorker,
    operation_name: str,
    extras: str,
) -> None:
    """Oneshot run."""
    await worker.start(register=False)

    extras_dict = ujson.loads(extras) if extras else {}

    LOG.info(
        'Running {!r} manually with extras {!r}',
        operation_name,
        extras_dict,
    )

    try:
        operation = so.SerialOperation.from_name(
            name=operation_name,
            extras=extras_dict,
        )
        executor = op.SerialOperationExecutor.from_operation(
            operation=operation,
            config=worker.config,
            mediator=worker.mediator,
        )
        await executor.execute()
    except (KeyboardInterrupt, asyncio.CancelledError):
        LOG.warning('Stopped manually')
    finally:
        await worker.stop()


async def run_automatic(worker: SerialWorker) -> None:
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
        LOG.warning('Stopped manually')
    finally:
        await worker.stop()


if __name__ == '__main__':
    app()
