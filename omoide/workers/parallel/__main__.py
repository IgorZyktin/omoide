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
from omoide.const import LockableResource
from omoide.infra.locators import FilesystemLocator
from omoide.object_storage.implementations.pg_large_object_content_storage import (
    PgLargeObjectStorage,
)
from omoide.object_storage.interfaces import AbsObjectStorage
from omoide.workers import utils
from omoide.workers.parallel import metrics
from omoide.workers.parallel import commands
from omoide import models
from omoide import const
from omoide.workers.parallel.cfg import ParallelWorkerConfig
from omoide.workers.parallel.commands.base_command import Command
from omoide.workers.parallel.database import ParallelPostgreSQLDatabase

LOG = custom_logging.get_logger(__name__)
WORKING = threading.Event()
WORKING.set()


async def main() -> None:
    """Async entry point."""
    config = ns.from_env(
        ParallelWorkerConfig, env_prefix='omoide_worker_parallel'
    )

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
    meta_repo = impl_sqlalchemy.MetaRepo()

    fs_locator = FilesystemLocator(
        root=config.data_folder,
        prefix_size=config.prefix_size,
    )

    object_storage = PgLargeObjectStorage(db)

    with executor, metrics_collector:
        async with db, lock:
            while WORKING.is_set():
                try:
                    did_something = await do_work(
                        config=config,
                        executor=executor,
                        lock=lock,
                        database=db,
                        metrics_collector=metrics_collector,
                        users_repo=users_repo,
                        items_repo=items_repo,
                        meta_repo=meta_repo,
                        fs_locator=fs_locator,
                        object_storage=object_storage,
                    )

                    if not did_something:
                        await asyncio.sleep(config.delay)
                except (KeyboardInterrupt, asyncio.CancelledError):
                    LOG.warning('Stopping manually')
                    break

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
    meta_repo: impl_sqlalchemy.MetaRepo,
    fs_locator: FilesystemLocator,
    object_storage: AbsObjectStorage,
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
                    executor=executor,
                    lock=lock,
                    database=database,
                    metrics_collector=metrics_collector,
                    users_repo=users_repo,
                    items_repo=items_repo,
                    meta_repo=meta_repo,
                    fs_locator=fs_locator,
                    object_storage=object_storage,
                )
            )

    return True


async def process_one(
    command: models.ParallelCommand,
    executor: ProcessPoolExecutor,
    lock: PGAdvisoryLock,
    database: ParallelPostgreSQLDatabase,
    metrics_collector: metrics.PrometheusMetricsCollector,
    users_repo: impl_sqlalchemy.UsersRepo,
    items_repo: impl_sqlalchemy.ItemsRepo,
    meta_repo: impl_sqlalchemy.MetaRepo,
    fs_locator: FilesystemLocator,
    object_storage: AbsObjectStorage,
) -> None:
    """Process one command."""
    try:
        await _process_one(
            command=command,
            executor=executor,
            lock=lock,
            database=database,
            metrics_collector=metrics_collector,
            users_repo=users_repo,
            items_repo=items_repo,
            meta_repo=meta_repo,
            fs_locator=fs_locator,
            object_storage=object_storage,
        )
    except Exception:
        LOG.exception('Command {} failed', command.id)
        traceback = custom_logging.capture_exception_output(
            f'Command {command.id} failed'
        )
        await database.mark_failed(command, traceback or '???')
        metrics_collector.increment(metrics.ERRORS, 1)


async def _process_one(
    command: models.ParallelCommand,
    executor: ProcessPoolExecutor,
    lock: PGAdvisoryLock,
    database: ParallelPostgreSQLDatabase,
    metrics_collector: metrics.PrometheusMetricsCollector,
    users_repo: impl_sqlalchemy.UsersRepo,
    items_repo: impl_sqlalchemy.ItemsRepo,
    meta_repo: impl_sqlalchemy.MetaRepo,
    fs_locator: FilesystemLocator,
    object_storage: AbsObjectStorage,
) -> None:
    """Process one command."""
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

        case models.Command.COPY_IMAGE:
            command_implementation = commands.CopyImageCommand(
                dto=command,
                database=database,
                users=users_repo,
                items=items_repo,
                meta=meta_repo,
                locator=fs_locator,
            )

        case models.Command.UPLOAD:
            command_implementation = commands.UploadCommand(
                dto=command,
                database=database,
                users=users_repo,
                items=items_repo,
                meta=meta_repo,
                locator=fs_locator,
                executor=executor,
                object_storage=object_storage,
            )

        case _:
            assert_never(command_type)

    resources = command_implementation.get_required_resources()

    if command.oid is not None:
        resources.append(
            LockableResource(const.LockNamespace.LARGE_OBJECTS, command.oid)
        )

    locks = await lock.acquire(resources)
    if locks is None:
        return

    try:
        if not await database.start_task(command):
            return

        start = time.perf_counter()
        bytes_processed = await command_implementation.execute()
        time_spent = time.perf_counter() - start

        await database.mark_done(command)
        LOG.info('Finished command {} ({})', command.id, command.name)

        metrics_collector.increment(metrics.COMMANDS_PROCESSED, 1)
        metrics_collector.increment(metrics.TIME_SPENT, int(time_spent * 1000))
        if bytes_processed:
            metrics_collector.increment(
                metrics.BYTES_PROCESSED, bytes_processed
            )

        if command.oid is not None:
            await _cleanup_oid(
                database, object_storage, command.oid, exclude_id=command.id
            )

    finally:
        await lock.release_held(locks)


async def _cleanup_oid(
    database: ParallelPostgreSQLDatabase,
    object_storage: AbsObjectStorage,
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
        await object_storage.delete(oid)


if __name__ == '__main__':
    asyncio.run(main())
