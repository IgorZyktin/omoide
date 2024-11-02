"""Worker that performs operations one by one."""

import asyncio
from typing import Annotated

import typer
import ujson

from omoide import custom_logging
from omoide import models
from omoide import utils
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common import runtime
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import cfg
from omoide.workers.serial import operations
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
    """Async entry point."""
    config = cfg.Config()
    mediator = WorkerMediator(
        database=sa.SqlalchemyDatabase(config.db_admin_url.get_secret_value()),
        items=sa.ItemsRepo(),
        tags=sa.TagsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
        misc=sa.MiscRepo(),
    )
    worker = SerialWorker(config, mediator)

    if operation:
        await run_manual(worker, operation, extras)
    else:
        await runtime.run_automatic(worker)


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
        operation = models.SerialOperation(
            id=-1,
            name=operation_name,
            worker_name='dev',
            status=models.OperationStatus.CREATED,
            extras=extras_dict,
            created_at=utils.now(),
            updated_at=utils.now(),
            started_at=None,
            ended_at=None,
            log=None,
        )
        implementation = operations.get_implementation(
            config=worker.config,
            operation=operation,
            mediator=worker.mediator,
        )
        await implementation.execute()
    except (KeyboardInterrupt, asyncio.CancelledError):
        LOG.warning('Stopped manually')
    finally:
        await worker.stop()


if __name__ == '__main__':
    app()
