"""Worker that performs operations in parallel."""

import asyncio
from concurrent.futures import ProcessPoolExecutor
import threading
import time
from typing import assert_never

import nano_settings as ns
import python_utilz as pu

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy
from omoide.infra.implementations.pg_advisory_lock import PGAdvisoryLock
from omoide.infra.interfaces.abs_lock import LockableResource
from omoide.infra.locators import FilesystemLocator
from omoide.workers import utils
from omoide.workers.worker_parallel import metrics
from omoide.workers.worker_parallel import commands
from omoide import models
from omoide.workers.worker_parallel.cfg import ParallelWorkerConfig
from omoide.workers.worker_parallel.commands.base_command import Command
from omoide.workers.worker_parallel.database import ParallelPostgreSQLDatabase

LOG = custom_logging.get_logger(__name__)
WORKING = threading.Event()
WORKING.set()

NAMESPACE_ITEMS = 1
NAMESPACE_LARGE_OBJECTS = 2


async def main() -> None:
    """Async entry point."""
    config = ns.from_env(ParallelWorkerConfig, env_prefix='owp')

    custom_logging.init_logging(
        level=config.log.level,
        diagnose=config.log.diagnose,
        path=config.log.path,
        rotation=config.log.rotation,
    )

    LOG.info('Started parallel worker: {}', config.name)

    utils.add_signal_handling(event=WORKING, deadline=config.shutdown_deadline)

    metrics_collector = metrics.get_metric_collector(
        address=config.metrics.address,
        port=config.metrics.port,
        name=config.name,
    )

    executor = utils.get_executor(config.workers, config.max_workers)

    db = ParallelPostgreSQLDatabase(
        db_url=config.db.url.get_secret_value(),
        echo=config.db.echo,
    )

    lock = PGAdvisoryLock(db_url=config.db.url.get_secret_value())

    users_repo = impl_sqlalchemy.UsersRepo()
    items_repo = impl_sqlalchemy.ItemsRepo()
    fs_locator = FilesystemLocator(
        root=config.data_folder,
        prefix_size=config.prefix_size,
    )

    with executor, metrics_collector:
        async with db, lock:
            while WORKING.is_set():
                did_something = await do_work(
                    config=config,
                    executor=executor,
                    lock=lock,
                    database=db,
                    metrics_collector=metrics_collector,
                    users_repo=users_repo,
                    items_repo=items_repo,
                    fs_locator=fs_locator,
                )

                if not did_something:
                    await asyncio.sleep(config.delay)

    LOG.info(
        'Worker {} stopped. Processed: {} tasks, {}, got {} errors.',
        config.name,
        pu.sep_digits(
            int(metrics_collector.get_value(metrics.COMMANDS_PROCESSED))
        ),
        pu.human_readable_size(
            metrics_collector.get_value(metrics.BYTES_PROCESSED)
        ),
        pu.sep_digits(
            int(metrics_collector.get_value(metrics.ERRORS)),
        ),
    )


async def do_work(
    config: ParallelWorkerConfig,
    executor: ProcessPoolExecutor,
    lock: PGAdvisoryLock,
    database: ParallelPostgreSQLDatabase,
    metrics_collector: metrics.PrometheusMetricsCollector,
    users_repo: impl_sqlalchemy.UsersRepo,
    items_repo: impl_sqlalchemy.ItemsRepo,
    fs_locator: FilesystemLocator,
) -> bool:
    """Perform workload."""
    candidates = await database.get_parallel_commands(
        batch_size=config.input_batch,
        supported_operations=config.supported_operations,
    )

    if not candidates:
        return False

    async with asyncio.TaskGroup() as tg:
        for candidate in candidates:
            tg.create_task(
                process_one(
                    command=candidate,
                    config=config,
                    executor=executor,
                    lock=lock,
                    database=database,
                    metrics_collector=metrics_collector,
                    users_repo=users_repo,
                    items_repo=items_repo,
                    fs_locator=fs_locator,
                )
            )

    return True


async def process_one(
    command: models.ParallelCommand,
    config: ParallelWorkerConfig,
    executor: ProcessPoolExecutor,
    lock: PGAdvisoryLock,
    database: ParallelPostgreSQLDatabase,
    metrics_collector: metrics.PrometheusMetricsCollector,
    users_repo: impl_sqlalchemy.UsersRepo,
    items_repo: impl_sqlalchemy.ItemsRepo,
    fs_locator: FilesystemLocator,
) -> None:
    """Process one command."""
    try:
        await _process_one(
            command=command,
            config=config,
            executor=executor,
            lock=lock,
            database=database,
            metrics_collector=metrics_collector,
            users_repo=users_repo,
            items_repo=items_repo,
            fs_locator=fs_locator,
        )
    except Exception:
        LOG.exception('Process_one for task {} crashed', command.id)


async def _process_one(
    command: models.ParallelCommand,
    config: ParallelWorkerConfig,
    executor: ProcessPoolExecutor,
    lock: PGAdvisoryLock,
    database: ParallelPostgreSQLDatabase,
    metrics_collector: metrics.PrometheusMetricsCollector,
    users_repo: impl_sqlalchemy.UsersRepo,
    items_repo: impl_sqlalchemy.ItemsRepo,
    fs_locator: FilesystemLocator,
) -> None:
    """Process one command."""
    resources = [LockableResource(NAMESPACE_ITEMS, command.item_id)]

    oid = command.extras.get('oid')
    if oid is not None:
        try:
            resources.append(
                LockableResource(NAMESPACE_LARGE_OBJECTS, int(oid))
            )
        except (TypeError, ValueError):
            LOG.error('Command {} has invalid oid: {!r}', command.id, oid)
            await database.mark_failed(command, f'Invalid oid: {oid!r}')
            return

    locks = await lock.acquire(resources)
    if locks is None:
        return

    try:
        if not await database.start_task(command):
            return

        try:
            start = time.perf_counter()
            warnings, bytes_processed = await dispatch_and_execute(
                command=command,
                config=config,
                executor=executor,
                database=database,
                users_repo=users_repo,
                items_repo=items_repo,
                fs_locator=fs_locator,
            )
            time_spent = time.perf_counter() - start
            await database.mark_done(command)
            succeeded = True
        except Exception:
            traceback = custom_logging.capture_exception_output(
                f'Command {command.id} failed'
            )
            LOG.exception('Command {} failed', command.id)
            await database.mark_failed(command, traceback or '???')
            metrics_collector.increment(metrics.ERRORS, 1)
            succeeded = False
        else:
            LOG.info('Finished command {} ({})', command.id, command.name)
            metrics_collector.increment(metrics.COMMANDS_PROCESSED, 1)
            metrics_collector.increment(
                metrics.TIME_SPENT, int(time_spent * 1000)
            )

            if bytes_processed:
                metrics_collector.increment(
                    metrics.BYTES_PROCESSED, bytes_processed
                )

            for warning in warnings:
                LOG.warning(
                    'Warning in task {} ({}): {}',
                    command.id,
                    command.name,
                    warning,
                )

        if oid and succeeded:
            await _cleanup_oid(database, oid, exclude_id=command.id)

    finally:
        await lock.release_held(locks)


async def _cleanup_oid(
    database: ParallelPostgreSQLDatabase,
    oid: int,
    exclude_id: int,
) -> None:
    """Delete oid from database."""
    if await database.is_oid_referenced_elsewhere(oid, exclude_id=exclude_id):
        LOG.info(
            'Keeping large object {} alive: '
            'still referenced by other queue entries',
            oid,
        )
    else:
        await database.delete_large_object(oid)


async def dispatch_and_execute(
    command: models.ParallelCommand,
    config: ParallelWorkerConfig,
    executor: ProcessPoolExecutor,
    database: ParallelPostgreSQLDatabase,
    users_repo: impl_sqlalchemy.UsersRepo,
    items_repo: impl_sqlalchemy.ItemsRepo,
    fs_locator: FilesystemLocator,
) -> tuple[list[str], int]:
    """Choose implementation and execute."""
    command_implementation: Command
    command_type = models.Command(command.name)
    match command_type:
        case models.Command.DUMMY:
            command_implementation = commands.DummyCommand(command)

        case models.Command.HARD_DELETE:
            command_implementation = commands.HardDeleteCommand(
                dto=command,
                database=database,
                users=users_repo,
                items=items_repo,
                locator=fs_locator,
            )

        case models.Command.SOFT_DELETE:
            command_implementation = commands.SoftDeleteCommand(
                dto=command,
                database=database,
                users=users_repo,
                items=items_repo,
                locator=fs_locator,
            )

        case _:
            assert_never(command_type)

    return await command_implementation.execute()


if __name__ == '__main__':
    asyncio.run(main())
