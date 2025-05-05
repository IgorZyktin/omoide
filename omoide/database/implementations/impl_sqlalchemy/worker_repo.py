"""Repository that perform worker-related operations."""

from collections.abc import Collection

import python_utilz as pu
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import exceptions
from omoide import operations
from omoide.database import db_models
from omoide.database.interfaces.abs_worker_repo import AbsWorkersRepo


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
    ) -> operations.BaseSerialOperation | None:
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

        for cls in operations.BaseSerialOperation.__subclasses__():
            if cls.name == response.name and issubclass(cls, operations.BaseSerialOperation):
                # TODO - mark operation as failed if got an exception here
                return cls.from_extras(  # type: ignore [return-value]
                    id=response.id,
                    name=response.name,
                    worker_name=response.worker_name,
                    status=operations.OperationStatus(response.status),
                    extras=response.extras,
                    created_at=response.created_at,
                    updated_at=response.updated_at,
                    started_at=response.started_at,
                    ended_at=response.ended_at,
                    log=response.log,
                    payload=response.payload,
                )

        raise exceptions.UnknownSerialOperationError(name=response.name)

    async def lock_serial_operation(
        self,
        conn: AsyncConnection,
        operation: operations.BaseSerialOperation,
        worker_name: str,
    ) -> bool:
        """Lock operation, return True on success."""
        now = pu.now()

        update_query = (
            sa.update(db_models.SerialOperation)
            .values(
                worker_name=worker_name,
                status=operations.OperationStatus.PROCESSING,
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
        operation: operations.BaseSerialOperation,
    ) -> int:
        """Save operation."""
        query = (
            sa.update(db_models.SerialOperation)
            .where(db_models.SerialOperation.id == operation.id)
            .values(
                worker_name=operation.worker_name,
                status=operation.status,
                extras=operation.extras,
                created_at=operation.created_at,
                updated_at=operation.updated_at,
                started_at=operation.started_at,
                ended_at=operation.ended_at,
                log=operation.log,
            )
        )
        response = await conn.execute(query)
        return int(response.rowcount)

    async def save_parallel_operation(
        self,
        conn: AsyncConnection,
        operation: operations.BaseParallelOperation,
        minimal_completion: set[str],
    ) -> int:
        """Save operation."""
        select_query = sa.select(db_models.ParallelOperation).where(
            db_models.ParallelOperation.id == operation.id
        )

        actual_operation = (await conn.execute(select_query)).fetchone()

        if actual_operation is None:
            raise exceptions.BadParallelOperationError(
                problem=f'lost track of parallel operation {operation.id}'
            )

        if (
            actual_operation.status == operations.OperationStatus.FAILED  # noqa: PLR1714
            or operation.status == operations.OperationStatus.FAILED
        ):
            status = operations.OperationStatus.FAILED
        else:
            status = operation.status

        processed_by = set(actual_operation.processed_by) | operation.processed_by

        if status == operations.OperationStatus.CREATED and processed_by >= minimal_completion:
            status = operations.OperationStatus.DONE

        query = (
            sa.update(db_models.ParallelOperation)
            .where(db_models.ParallelOperation.id == operation.id)
            .values(
                status=status,
                extras=operation.extras,
                created_at=operation.created_at,
                updated_at=operation.updated_at,
                started_at=operation.started_at,
                ended_at=operation.ended_at,
                log='\n'.join([actual_operation.log or '', operation.log or '']),
                payload=operation.payload,
                processed_by=sorted(processed_by),
            )
        )
        response = await conn.execute(query)
        rows_changed = int(response.rowcount)

        if not rows_changed:
            raise exceptions.BadParallelOperationError(
                problem=f'lost track of parallel operation {operation.id}'
            )

        return rows_changed

    async def get_next_parallel_batch(
        self,
        conn: AsyncConnection,
        worker_name: str,
        names: Collection[str],
        batch_size: int,
    ) -> list[operations.BaseParallelOperation]:
        """Return next parallel operation batch."""
        select_query = (
            sa.select(db_models.ParallelOperation)
            .where(
                db_models.ParallelOperation.status == operations.OperationStatus.CREATED,
                db_models.ParallelOperation.name.in_(tuple(names)),
                sa.not_(db_models.ParallelOperation.processed_by.any_() == worker_name),
            )
            .order_by(db_models.ParallelOperation.id)
            .limit(batch_size)
        )

        response = (await conn.execute(select_query)).fetchall()

        cls_cache: dict[str, type[operations.BaseParallelOperation]] = {}
        instances: list[operations.BaseParallelOperation] = []

        for each in response:
            # TODO - mark each as failed if got an exception here
            cls = cls_cache.get(each.name)

            if cls is None:
                for each_cls in operations.BaseParallelOperation.__subclasses__():
                    if (
                        issubclass(each_cls, operations.BaseParallelOperation)
                        and each_cls.name == each.name
                    ):
                        cls_cache[each.name] = each_cls
                        cls = each_cls

            if cls is None:
                raise exceptions.UnknownParallelOperationError(name=each.name)

            if issubclass(cls, operations.BaseParallelOperation):
                instance = cls.from_extras(
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
                    processed_by=set(each.processed_by),
                )

                instances.append(instance)  # type: ignore [arg-type]

        return instances
