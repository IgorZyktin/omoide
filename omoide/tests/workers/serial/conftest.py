"""Serial worker fixtures."""

import os

import pytest
import pytest_asyncio

from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import cfg
from omoide.workers.serial.worker import SerialWorker


@pytest.fixture(scope='session')
def serial_worker_config() -> cfg.Config:
    """Return configured instance."""
    env_var = 'OMOIDE_DB_URL_TEST'
    db_name = 'omoide_test'
    db_url = os.environ.get(env_var)

    if not db_url:
        msg = f'You have to specify test database using variable {env_var}'
        raise RuntimeError(msg)

    if not db_url.endswith(db_name):
        msg = (
            "Are you sure you're using test "
            f"database? URL must end with {db_name}"
        )
        raise RuntimeError(msg)

    return cfg.Config(
        db_admin_url=db_url,
        name='test',
        short_delay=0.0,
        long_delay=0.001,
        input_batch=10,
        output_batch=10,
        supported_operations=[
            'dummy',
            'rebuild_known_tags_anon',
            'rebuild_known_tags_user',
            'rebuild_known_tags_all',
            'update_permissions',
        ]
    )


@pytest.fixture(scope='session')
def serial_worker_mediator(serial_worker_config) -> WorkerMediator:
    """Return configured instance."""
    return WorkerMediator(
        database=sa.SqlalchemyDatabase(
            db_url=serial_worker_config.db_admin_url.get_secret_value()
        ),
        items=sa.ItemsRepo(),
        tags=sa.TagsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
    )


@pytest_asyncio.fixture(scope='session')
async def serial_worker(
    serial_worker_config,
    serial_worker_mediator,
) -> SerialWorker:
    """Return configured instance."""
    worker = SerialWorker(
        config=serial_worker_config,
        mediator=serial_worker_mediator,
    )
    try:
        await worker.start(register=False)
        yield worker
    finally:
        await worker.stop()
