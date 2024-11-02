"""Repository that perform worker-related operations."""

from collections.abc import Collection

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.database import db_models
from omoide.database.interfaces.abs_worker_repo import AbsWorkersRepo


class WorkersRepo(AbsWorkersRepo[AsyncConnection]):
    """Repository that perform worker-related operations."""

    async def register_worker(self, conn: AsyncConnection, worker_name: str) -> None:
        """Ensure we're allowed to run and update starting time."""
        stmt = (
            sa.update(db_models.RegisteredWorkers)
            .values(last_restart=utils.now())
            .where(db_models.RegisteredWorkers.worker_name == worker_name)
        )

        response = await conn.execute(stmt)

        if not response.rowcount:
            raise exceptions.UnknownWorkerError(worker_name=worker_name)

    async def take_serial_lock(self, conn: AsyncConnection, worker_name: str) -> bool:
        """Try acquiring the lock, return True on success."""
        stmt = sa.update(db_models.SerialLock).values(
            worker_name=worker_name,
            last_update=utils.now(),
        )
        response = await conn.execute(stmt)
        return bool(response.rowcount)

    async def release_serial_lock(self, conn: AsyncConnection, worker_name: str) -> bool:
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
        names: Collection[str],
    ) -> models.SerialOperation | None:
        """Try locking next serial operation."""
        select_query = (
            sa.select(db_models.SerialOperation)
            .where(
                db_models.SerialOperation.status == models.OperationStatus.CREATED,
                db_models.SerialOperation.name.in_(tuple(names)),
            )
            .order_by(db_models.SerialOperation.id)
            .limit(1)
        )

        response = (await conn.execute(select_query)).fetchone()

        if response is None:
            return None

        return models.SerialOperation.from_obj(response)

    async def lock_serial_operation(
        self,
        conn: AsyncConnection,
        operation: models.SerialOperation,
        worker_name: str,
    ) -> bool:
        """Lock operation, return True on success."""
        now = utils.now()

        update_query = (
            sa.update(db_models.SerialOperation)
            .values(
                worker_name=worker_name,
                status=models.OperationStatus.PROCESSING,
                updated_at=now,
                started_at=now,
            )
            .where(db_models.SerialOperation.id == operation.id)
        )

        response = await conn.execute(update_query)
        return bool(response.rowcount)

    async def save_serial_operation(
        self,
        conn: AsyncConnection,
        operation: models.SerialOperation,
    ) -> int:
        """Save operation."""
        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(**operation.get_changes())
        )
        response = await conn.execute(query)
        return int(response.rowcount)

    async def get_next_parallel_batch(
        self,
        conn: AsyncConnection,
        worker_name: str,
        names: Collection[str],
        batch_size: int,
    ) -> list[models.ParallelOperation]:
        """Return next parallel operation batch."""
        select_query = (
            sa.select(db_models.ParallelOperation)
            .where(
                sa.or_(
                    db_models.ParallelOperation.status == models.OperationStatus.CREATED,
                    db_models.ParallelOperation.status == models.OperationStatus.PROCESSING,
                ),
                db_models.ParallelOperation.name.in_(tuple(names)),
                ~db_models.ParallelOperation.processed_by.any_() == worker_name,
            )
            .order_by(db_models.ParallelOperation.id)
            .limit(batch_size)
        )

        response = (await conn.execute(select_query)).fetchall()
        return [models.ParallelOperation.from_obj(raw) for raw in response]
