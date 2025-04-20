"""Worker that performs operations in parallel."""

import asyncio
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
import os

import nano_settings as ns
import typer

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy as sa
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
    config = ns.from_env(ParallelWorkerConfig, env_prefix='omoide_parallel_worker')

    custom_logging.init_logging(
        level=config.log_level,
        diagnose=config.log_diagnose,
        path=config.log_path,
        rotation=config.log_rotation,
    )

    mediator = WorkerMediator(
        database=sa.SqlalchemyDatabase(config.db_url.get_secret_value()),
        items=sa.ItemsRepo(),
        tags=sa.TagsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
        misc=sa.MiscRepo(),
    )

    workers = config.workers or os.cpu_count() or 1
    workers = min(workers, config.max_workers)

    executor: ProcessPoolExecutor | ThreadPoolExecutor
    if config.fork_type == 'process':
        executor = ProcessPoolExecutor(max_workers=workers)
    else:
        executor = ThreadPoolExecutor(max_workers=workers)

    worker = ParallelWorker(config, mediator, name=config.name, executor=executor)
    await worker.run(short_delay=config.short_delay, long_delay=config.long_delay)


if __name__ == '__main__':
    app()
