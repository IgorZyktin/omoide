"""Worker that performs operations in parallel."""

import asyncio
import os

import typer

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common import runtime
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.parallel.worker import ParallelWorker
from omoide.workers.parallel import cfg
from concurrent.futures import ProcessPoolExecutor

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


@app.command()
def main() -> None:
    """Entry point."""
    asyncio.run(_main())


async def _main() -> None:
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

    if config.workers is None:
        workers = os.cpu_count()
    else:
        workers = config.workers

    workers = min((workers or 1), config.max_workers)
    executor = ProcessPoolExecutor(max_workers=workers)
    worker = ParallelWorker(config, mediator, executor)
    await runtime.run_automatic(worker)


if __name__ == '__main__':
    app()
