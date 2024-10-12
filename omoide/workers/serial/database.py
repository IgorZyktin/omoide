"""Database for serial operations."""

import sqlalchemy as sa

from omoide import utils
from omoide.storage.database import db_models
from omoide.workers.common.base_db import BaseWorkerDatabase
from omoide.workers.serial.cfg import Config
from omoide.workers.serial.operations.base_operation import Operation
from omoide.workers.serial.operations.base_operation import Status


class SerialDatabase(BaseWorkerDatabase[Config]):
    """Database for serial operations."""

    async def take_lock(self) -> bool:
        """Try acquiring the lock."""
        query = sa.update(db_models.SerialLock).values(
            worker_name=self.config.name,
            last_update=utils.now(),
        )

        async with self._engine.begin() as conn:
            response = await conn.execute(query)

        return bool(response.rowcount)

    async def release_lock(self) -> bool:
        """Try releasing the lock."""
        query = sa.update(db_models.SerialLock).values(
            worker_name=None,
            last_update=utils.now(),
        )

        async with self._engine.begin() as conn:
            response = await conn.execute(query)

        return bool(response.rowcount)

    async def get_next_operation(self) -> Operation | None:
        """Try locking next operation."""
        select_query = (
            sa.select(db_models.SerialOperation)
            .where(db_models.SerialOperation.status == str(Status.CREATED))
            .order_by(db_models.SerialOperation.id)
            .limit(1)
        )

        async with self._engine.begin() as conn:
            operation = (await conn.execute(select_query)).fetchone()

            if operation is None:
                return None

        now = utils.now()

        update_query = (
            sa.update(db_models.SerialOperation)
            .values(
                worker_name=self.config.name,
                status=str(Status.PROCESSING),
                updated_at=now,
                started_at=now,
            )
            .where(db_models.SerialOperation.id == operation.id)
        )

        async with self._engine.begin() as conn:
            await conn.execute(update_query)

        return Operation.from_raw(
            id=operation.id,
            name=operation.operation,
            status=Status.from_string(operation.status),
            expected=operation.expected,
            affected=operation.affected,
            extras=operation.extras,
            created_at=operation.created_at,
            updated_at=operation.updated_at,
            started_at=operation.started_at,
            ended_at=operation.ended_at,
            log=operation.log,
        )

    async def complete_operation(self, operation: Operation) -> None:
        """Mark operation as complete."""
        now = utils.now()

        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(
                status=str(Status.DONE),
                updated_at=now,
                ended_at=now,
                affected=operation.affected,
                log=operation.log,
            )
        )

        async with self._engine.begin() as conn:
            await conn.execute(query)

    async def fail_operation(self, operation: Operation, error: str) -> None:
        """Mark operation as complete."""
        now = utils.now()

        if operation.log:
            operation.log += f'\n{error}'
        else:
            operation.log = error

        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(
                status=str(Status.FAILED),
                updated_at=now,
                ended_at=now,
                log=operation.log,
            )
        )

        async with self._engine.begin() as conn:
            await conn.execute(query)
