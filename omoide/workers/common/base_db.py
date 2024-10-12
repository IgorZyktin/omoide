"""Base database wrapper for all workers."""

import abc
from typing import Generic
from typing import TypeVar

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from omoide import utils
from omoide.storage.database import db_models

ConfigT = TypeVar('ConfigT')


class BaseWorkerDatabase(Generic[ConfigT], abc.ABC):
    """Base database wrapper for all workers."""

    def __init__(self, config: ConfigT) -> None:
        """Initialize instance."""
        self.config = config
        self._engine = create_async_engine(
            self.config.db_admin_url.get_secret_value(),
            pool_pre_ping=True,
        )

    async def connect(self) -> None:
        """Connect to the database."""

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        await self._engine.dispose()

    async def register_worker(self) -> None:
        """Ensure we're allowed to run."""
        query = sa.update(
            db_models.RegisteredWorkers
        ).values(
            last_restart=utils.now()
        ).where(
            db_models.RegisteredWorkers.worker_name == self.config.name
        )

        async with self._engine.begin() as conn:
            response = await conn.execute(query)

        if not response.rowcount:
            msg = (
                f'Worker {self.config.name} is not '
                'in list of registered workers'
            )
            raise RuntimeError(msg)
