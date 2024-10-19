"""Repository that perform worker-related operations."""

import sqlalchemy as sa

from omoide import exceptions
from omoide import utils
from omoide.database.interfaces.abs_worker_repo import AbsWorkerRepo
from omoide.models import OperationStatus
from omoide.models import SerialOperation
from omoide.database import db_models
from sqlalchemy.ext.asyncio import AsyncConnection


class WorkerRepo(AbsWorkerRepo[AsyncConnection]):
    """Repository that perform worker-related operations."""

    async def register_worker(
        self,
        conn: AsyncConnection,
        worker_name: str,
    ) -> None:
        """Ensure we're allowed to run and update starting time."""
        query = (
            sa.update(db_models.RegisteredWorkers)
            .values(last_restart=utils.now())
            .where(db_models.RegisteredWorkers.worker_name == worker_name)
        )

        response = await conn.execute(query)

        if not response.rowcount:
            raise exceptions.UnknownWorkerError(worker_name=worker_name)

    async def take_serial_lock(
        self,
        conn: AsyncConnection,
        worker_name: str,
    ) -> bool:
        """Try acquiring the lock, return True on success."""
        query = sa.update(db_models.SerialLock).values(
            worker_name=worker_name,
            last_update=utils.now(),
        )
        response = await conn.execute(query)
        return bool(response.rowcount)

    async def release_serial_lock(
        self,
        conn: AsyncConnection,
        worker_name: str,
    ) -> bool:
        """Try releasing the lock, return True on success."""
        query = (
            sa.update(db_models.SerialLock)
            .values(
                worker_name=None,
                last_update=utils.now(),
            )
            .where(
                db_models.SerialLock.worker_name == worker_name,
            )
        )
        response = await conn.execute(query)
        return bool(response.rowcount)

    async def get_next_serial_operation(
        self,
        conn: AsyncConnection,
    ) -> SerialOperation | None:
        """Try locking next serial operation."""
        select_query = (
            sa.select(db_models.SerialOperation)
            .where(db_models.SerialOperation.status == OperationStatus.CREATED)
            .order_by(db_models.SerialOperation.id)
            .limit(1)
        )

        operation = (await conn.execute(select_query)).fetchone()

        if operation is None:
            return None

        return SerialOperation.from_name(
            id=operation.id,
            name=operation.name,
            worker_name=operation.worker_name,
            status=OperationStatus(operation.status),
            extras=operation.extras,
            created_at=operation.created_at,
            updated_at=operation.updated_at,
            started_at=operation.started_at,
            ended_at=operation.ended_at,
            log=operation.log,
        )

    async def lock_serial_operation(
        self,
        conn: AsyncConnection,
        operation: SerialOperation,
        worker_name: str,
    ) -> bool:
        """Lock operation, return True on success."""
        now = utils.now()

        update_query = (
            sa.update(db_models.SerialOperation)
            .values(
                worker_name=worker_name,
                status=OperationStatus.PROCESSING,
                updated_at=now,
                started_at=now,
            )
            .where(db_models.SerialOperation.id == operation.id)
        )

        response = await conn.execute(update_query)
        return bool(response.rowcount)

    async def mark_serial_operation_done(
        self,
        conn: AsyncConnection,
        operation: SerialOperation,
    ) -> SerialOperation:
        """Mark operation as done."""
        now = utils.now()

        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(
                status=OperationStatus.DONE,
                updated_at=now,
                ended_at=now,
                log=operation.log,
            )
        )

        operation.updated_at = now
        operation.ended_at = now

        await conn.execute(query)
        return operation

    async def mark_serial_operation_failed(
        self,
        conn: AsyncConnection,
        operation: SerialOperation,
        error: str,
    ) -> SerialOperation:
        """Mark operation as failed."""
        now = utils.now()

        if operation.log:
            operation.log += f'\n{error}'
        else:
            operation.log = error

        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(
                status=OperationStatus.FAILED,
                updated_at=now,
                ended_at=now,
                log=operation.log,
            )
        )

        operation.updated_at = now
        operation.ended_at = now

        await conn.execute(query)
        return operation
