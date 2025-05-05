"""Worker that performs operations one by one."""

import asyncio

import nano_settings as ns

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.object_storage.implementations.file_client import FileObjectStorageClient
from omoide.workers.common.worker import Worker
from omoide.workers.serial import loop_logic
from omoide.workers.serial.cfg import SerialWorkerConfig
from omoide.workers.serial.mediator import SerialWorkerMediator

LOG = custom_logging.get_logger(__name__)


async def main() -> None:
    """Async entry point."""
    config = ns.from_env(SerialWorkerConfig, env_prefix='omoide_serial_worker')

    custom_logging.init_logging(
        level=config.log_level,
        diagnose=config.log_diagnose,
        path=config.log_path,
        rotation=config.log_rotation,
    )

    mediator = SerialWorkerMediator(
        database=sa.SqlalchemyDatabase(config.db_url.get_secret_value()),
        exif=sa.EXIFRepo(),
        items=sa.ItemsRepo(),
        meta=sa.MetaRepo(),
        misc=sa.MiscRepo(),
        object_storage=FileObjectStorageClient(config.data_folder, config.prefix_size),
        signatures=sa.SignaturesRepo(),
        tags=sa.TagsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
    )

    worker = Worker(
        database=mediator.database,
        workers=mediator.workers,
        name=config.name,
        loop_callable=loop_logic.SerialOperationsProcessor(config, mediator),
    )

    try:
        await worker.start()
        await worker.run(short_delay=config.short_delay, long_delay=config.long_delay)
    finally:
        async with mediator.database.transaction() as conn:
            lock = await mediator.workers.release_serial_lock(
                conn=conn,
                worker_name=config.name,
            )
            if lock:
                LOG.info('Worker {!r} released lock', config.name)

        await worker.stop()


if __name__ == '__main__':
    asyncio.run(main())
