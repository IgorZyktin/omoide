"""Worker that performs operations one by one."""

import asyncio
from typing import Annotated

import python_utilz as pu
import typer
import ujson

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common import runtime
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import SerialWorkerConfig
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
    config = pu.from_env(SerialWorkerConfig, env_prefix='omoide_serial_worker')

    mediator = WorkerMediator(
        database=sa.SqlalchemyDatabase(config.db_url.get_secret_value()),
        items=sa.ItemsRepo(),
        tags=sa.TagsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
        misc=sa.MiscRepo(),
    )
    worker = SerialWorker(config, mediator, name=config.name)

    if operation:
        await run_manual(worker, operation, extras)
    else:
        await runtime.run_automatic(
            worker=worker,
            short_delay=config.short_delay,
            long_delay=config.long_delay,
        )


async def run_manual(worker: SerialWorker, operation_name: str, extras: str) -> None:
    """Oneshot run."""
    await worker.start(register=False)

    extras_dict = ujson.loads(extras) if extras else {}
    LOG.info('Manually running {!r} with extras {!r}', operation_name, extras_dict)

    try:
        await worker.run_use_case(operation_name, extras_dict)
    except (KeyboardInterrupt, asyncio.CancelledError):
        LOG.warning('Stopped manually')
    finally:
        await worker.stop()


if __name__ == '__main__':
    app()
