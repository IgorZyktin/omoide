"""Worker that performs operations in parallel."""

import asyncio
from concurrent.futures import ProcessPoolExecutor
import os

import python_utilz as pu
import typer

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common import runtime
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.parallel.cfg import ParallelWorkerConfig
from omoide.workers.parallel.worker import ParallelWorker

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


@app.command()
def main() -> None:
    """Entry point."""
    asyncio.run(_main())


async def _main() -> None:
    """Async entry point."""
    config = pu.from_env(ParallelWorkerConfig, env_prefix='omoide_parallel_worker')

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
        workers = os.cpu_count()

    workers = min((workers or 1), config.max_workers)
    executor = ProcessPoolExecutor(max_workers=workers)
    worker = ParallelWorker(config, mediator, name=config.name, executor=executor)
    await runtime.run_automatic(
        worker=worker,
        short_delay=config.short_delay,
        long_delay=config.long_delay,
    )


if __name__ == '__main__':
    app()
