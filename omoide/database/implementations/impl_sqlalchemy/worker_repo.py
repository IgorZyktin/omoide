"""Repository that perform worker-related operations."""

from collections.abc import Collection

import python_utilz as pu
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import custom_logging
from omoide import exceptions
from omoide import operations
from omoide.database import db_models
from omoide.database.interfaces.abs_worker_repo import AbsWorkersRepo

LOG = custom_logging.get_logger(__name__)


class WorkersRepo(AbsWorkersRepo[AsyncConnection]):
    """Repository that perform worker-related operations."""

    async def register_worker(self, conn: AsyncConnection, worker_name: str) -> None:
        """Ensure we're allowed to run and update starting time."""
        stmt = (
            sa.update(db_models.RegisteredWorkers)
            .values(last_restart=pu.now())
            .where(db_models.RegisteredWorkers.worker_name == worker_name)
        )

        response = await conn.execute(stmt)

        if not response.rowcount:
            raise exceptions.UnknownWorkerError(worker_name=worker_name)

    async def take_serial_lock(self, conn: AsyncConnection, worker_name: str) -> bool:
        """Try acquiring the lock, return True on success."""
        stmt = sa.update(db_models.SerialLock).values(
            worker_name=worker_name,
            last_update=pu.now(),
        )
        response = await conn.execute(stmt)
        return bool(response.rowcount)

    async def release_serial_lock(self, conn: AsyncConnection, worker_name: str) -> bool:
        """Try releasing the lock, return True on success."""
        query = (
            sa.update(db_models.SerialLock)
            .values(
                worker_name=None,
                last_update=pu.now(),
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
        skip: set[int],
    ) -> operations.Operation | None:
        """Try locking next serial operation."""
        select_query = (
            sa.select(db_models.SerialOperation)
            .where(
                db_models.SerialOperation.status == operations.OperationStatus.CREATED,
                db_models.SerialOperation.name.in_(tuple(names)),
                sa.not_(db_models.SerialOperation.name.in_(tuple(skip))),
            )
            .order_by(db_models.SerialOperation.id)
            .limit(1)
        )

        response = (await conn.execute(select_query)).fetchone()

        if response is None:
            return None

        return operations.Operation(
            id=response.id,
            name=response.name,
            status=operations.OperationStatus(response.status),
            extras=response.extras,
            created_at=response.created_at,
            updated_at=response.updated_at,
            started_at=response.started_at,
            ended_at=response.ended_at,
            log=response.log,
            payload=response.payload,
            processed_by=response.processed_by,
        )

    async def lock_serial_operation(
        self,
        conn: AsyncConnection,
        operation: operations.Operation,
    ) -> bool:
        """Lock operation, return True on success."""
        now = pu.now()

        update_query = (
            sa.update(db_models.SerialOperation)
            .values(
                status=operations.OperationStatus.PROCESSING,
                updated_at=now,
                started_at=now,
            )
            .where(db_models.SerialOperation.id == operation.id)
        )

        response = await conn.execute(update_query)
        return bool(response.rowcount)

    async def save_serial_operation_as_started(
        self,
        conn: AsyncConnection,
        operation: operations.Operation,
    ) -> int:
        """Save operation."""
        now = pu.now()

        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(
                status=operations.OperationStatus.PROCESSING.value,
                updated_at=now,
                started_at=now,
            )
        )
        response = await conn.execute(query)
        return int(response.rowcount)

    async def save_serial_operation_as_completed(
        self,
        conn: AsyncConnection,
        operation: operations.Operation,
        processed_by: str,
    ) -> int:
        """Save operation."""
        now = pu.now()

        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(
                status=operations.OperationStatus.DONE.value,
                updated_at=now,
                ended_at=now,
                processed_by=[processed_by],
                payload=b'',
            )
        )
        response = await conn.execute(query)
        return int(response.rowcount)

    async def save_serial_operation_as_failed(
        self,
        conn: AsyncConnection,
        operation: operations.Operation,
        error: str,
    ) -> int:
        """Save operation."""
        now = pu.now()

        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(
                status=operations.OperationStatus.FAILED.value,
                updated_at=now,
                ended_at=now,
                log=error,
            )
        )
        response = await conn.execute(query)
        return int(response.rowcount)

    async def save_parallel_operation_as_started(
        self,
        conn: AsyncConnection,
        operation: operations.Operation,
    ) -> int:
        """Start operation."""
        select_query = sa.select(db_models.ParallelOperation).where(
            db_models.ParallelOperation.id == operation.id
        )

        actual_operation = (await conn.execute(select_query)).fetchone()

        if actual_operation is None:
            LOG.warning('Lost track of parallel operation {}', operation)
            return 0

        if actual_operation.status == operations.OperationStatus.FAILED:
            return 0

        if actual_operation.status not in (
            operations.OperationStatus.DONE,
            operations.OperationStatus.FAILED,
        ):
            status = operations.OperationStatus.PROCESSING
        else:
            status = actual_operation.status

        now = pu.now()

        query = (
            sa.update(db_models.ParallelOperation)
            .where(db_models.ParallelOperation.id == operation.id)
            .values(
                status=status,
                updated_at=now,
                started_at=now,
            )
        )
        response = await conn.execute(query)
        rows_changed = int(response.rowcount)

        if not rows_changed:
            LOG.warning('Lost track of parallel operation {}', operation)
            return 0

        return rows_changed

    async def save_parallel_operation_as_complete(
        self,
        conn: AsyncConnection,
        operation: operations.Operation,
        minimal_completion: set[str],
        processed_by: str,
    ) -> tuple[int, bool]:
        """Save operation."""
        select_query = sa.select(db_models.ParallelOperation).where(
            db_models.ParallelOperation.id == operation.id
        )

        actual_operation = (await conn.execute(select_query)).fetchone()

        if actual_operation is None:
            LOG.warning('Lost track of parallel operation {}', operation)
            return 0, False

        if actual_operation.status == operations.OperationStatus.FAILED.value:
            return 0, False

        processed_by_set = set(actual_operation.processed_by) | {processed_by}

        is_done = False
        if (
            actual_operation.status
            in (
                operations.OperationStatus.CREATED.value,
                operations.OperationStatus.PROCESSING.value,
            )
            and processed_by_set >= minimal_completion
        ):
            status = operations.OperationStatus.DONE.value
            is_done = True
        else:
            status = actual_operation.status

        now = pu.now()

        query = (
            sa.update(db_models.ParallelOperation)
            .where(db_models.ParallelOperation.id == operation.id)
            .values(
                status=status,
                updated_at=now,
                ended_at=now,
                processed_by=sorted(processed_by_set),
                payload=b'',
            )
        )
        response = await conn.execute(query)
        rows_changed = int(response.rowcount)

        if not rows_changed:
            LOG.warning('Lost track of parallel operation {}', operation)
            return 0, False

        return rows_changed, is_done

    async def save_parallel_operation_as_failed(
        self,
        conn: AsyncConnection,
        operation: operations.Operation,
        error: str,
    ) -> int:
        """Save operation."""
        select_query = sa.select(db_models.ParallelOperation).where(
            db_models.ParallelOperation.id == operation.id
        )

        actual_operation = (await conn.execute(select_query)).fetchone()

        if actual_operation is None:
            LOG.warning('Lost track of parallel operation {}', operation)
            return 0

        if actual_operation.status == operations.OperationStatus.FAILED.value:
            return 0

        now = pu.now()

        query = (
            sa.update(db_models.ParallelOperation)
            .where(db_models.ParallelOperation.id == operation.id)
            .values(
                status=operations.OperationStatus.FAILED,
                updated_at=now,
                ended_at=now,
                log='\n'.join([actual_operation.log or '', error]),
            )
        )
        response = await conn.execute(query)
        rows_changed = int(response.rowcount)

        if not rows_changed:
            LOG.warning('Lost track of parallel operation {}', operation)
            return 0

        return rows_changed

    async def get_next_parallel_batch(
        self,
        conn: AsyncConnection,
        worker_name: str,
        names: Collection[str],
        batch_size: int,
    ) -> list[operations.Operation]:
        """Return next parallel operation batch."""
        select_query = (
            sa.select(db_models.ParallelOperation)
            .where(
                sa.or_(
                    db_models.ParallelOperation.status == operations.OperationStatus.CREATED.value,
                    db_models.ParallelOperation.status
                    == operations.OperationStatus.PROCESSING.value,
                ),
                db_models.ParallelOperation.name.in_(tuple(names)),
                sa.not_(db_models.ParallelOperation.processed_by.any_() == worker_name),
            )
            .order_by(db_models.ParallelOperation.id)
            .limit(batch_size)
        )

        response = (await conn.execute(select_query)).fetchall()

        return [
            operations.Operation(
                id=each.id,
                name=each.name,
                status=operations.OperationStatus(each.status),
                extras=each.extras,
                created_at=each.created_at,
                updated_at=each.updated_at,
                started_at=each.started_at,
                ended_at=each.ended_at,
                log=each.log,
                payload=each.payload,
                processed_by=each.processed_by,
            )
            for each in response
        ]
