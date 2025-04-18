"""Worker that performs operations in parallel."""

import asyncio
from concurrent.futures import ProcessPoolExecutor
import os
from typing import Annotated

import nano_settings as ns
import typer
import ujson

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common import runtime
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.parallel.cfg import ParallelWorkerConfig
from omoide.workers.parallel.worker import ParallelWorker

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
    config = ns.from_env(ParallelWorkerConfig, env_prefix='omoide_parallel_worker')

    mediator = WorkerMediator(
        database=sa.SqlalchemyDatabase(config.db_url.get_secret_value()),
        items=sa.ItemsRepo(),
        tags=sa.TagsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
        misc=sa.MiscRepo(),
    )

    if config.workers:
        workers = config.workers
    else:
        workers = os.cpu_count() or 1

    workers = min((workers or 1), config.max_workers)
    executor = ProcessPoolExecutor(max_workers=workers)
    worker = ParallelWorker(config, mediator, name=config.name, executor=executor)

    if operation:
        await run_manual(worker, operation, extras)
    else:
        await runtime.run_automatic(
            worker=worker,
            short_delay=config.short_delay,
            long_delay=config.long_delay,
        )


async def run_manual(worker: ParallelWorker, operation_name: str, extras: str) -> None:
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
