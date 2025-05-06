"""Worker that performs operations in parallel."""

import asyncio
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
import os

import nano_settings as ns

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common.worker import Worker
from omoide.workers.parallel import loop_logic
from omoide.workers.parallel.cfg import ParallelWorkerConfig
from omoide.workers.parallel.mediator import ParallelWorkerMediator


async def main() -> None:
    """Async entry point."""
    config = ns.from_env(ParallelWorkerConfig, env_prefix='omoide_parallel_worker')

    custom_logging.init_logging(
        level=config.log_level,
        diagnose=config.log_diagnose,
        path=config.log_path,
        rotation=config.log_rotation,
    )

    mediator = ParallelWorkerMediator(
        database=sa.SqlalchemyDatabase(config.db_url.get_secret_value()),
        items=sa.ItemsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
        misc=sa.MiscRepo(),
        signatures=sa.SignaturesRepo(),
    )

    cores = config.workers or os.cpu_count() or 1
    cores = min(cores, config.max_workers)

    executor: ProcessPoolExecutor | ThreadPoolExecutor
    if config.fork_type == 'process':
        executor = ProcessPoolExecutor(max_workers=cores)
    else:
        executor = ThreadPoolExecutor(max_workers=cores)

    worker = Worker(
        database=mediator.database,
        workers=mediator.workers,
        name=config.name,
        loop_callable=loop_logic.ParallelOperationsProcessor(config, mediator, executor),
    )

    try:
        await worker.start()
        await worker.run(short_delay=config.short_delay, long_delay=config.long_delay)
    finally:
        executor.shutdown()
        await worker.stop()


if __name__ == '__main__':
    asyncio.run(main())
