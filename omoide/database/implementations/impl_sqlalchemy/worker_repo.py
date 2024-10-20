"""Repository that perform worker-related operations."""

from typing import Collection

import sqlalchemy as sa
from sqlalchemy import Connection

from omoide import exceptions
from omoide import utils
from omoide.database import db_models
from omoide.database.interfaces.abs_worker_repo import AbsWorkersRepo
from omoide.models import OperationStatus
from omoide.models import SerialOperation


class WorkersRepo(AbsWorkersRepo[Connection]):
    """Repository that perform worker-related operations."""

    def register_worker(
        self,
        conn: Connection,
        worker_name: str,
    ) -> None:
        """Ensure we're allowed to run and update starting time."""
        query = (
            sa.update(db_models.RegisteredWorkers)
            .values(last_restart=utils.now())
            .where(db_models.RegisteredWorkers.worker_name == worker_name)
        )

        response = conn.execute(query)

        if not response.rowcount:
            raise exceptions.UnknownWorkerError(worker_name=worker_name)

    def take_serial_lock(
        self,
        conn: Connection,
        worker_name: str,
    ) -> bool:
        """Try acquiring the lock, return True on success."""
        query = sa.update(db_models.SerialLock).values(
            worker_name=worker_name,
            last_update=utils.now(),
        )
        response = conn.execute(query)
        return bool(response.rowcount)

    def release_serial_lock(
        self,
        conn: Connection,
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
        response = conn.execute(query)
        return bool(response.rowcount)

    def get_next_serial_operation(
        self,
        conn: Connection,
        names: Collection[str],
    ) -> SerialOperation | None:
        """Try locking next serial operation."""
        select_query = (
            sa.select(db_models.SerialOperation)
            .where(
                db_models.SerialOperation.status == OperationStatus.CREATED,
                db_models.SerialOperation.name.in_(tuple(names)),
            )
            .order_by(db_models.SerialOperation.id)
            .limit(1)
        )

        operation = conn.execute(select_query).fetchone()

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

    def lock_serial_operation(
        self,
        conn: Connection,
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

        response = conn.execute(update_query)
        return bool(response.rowcount)

    def mark_serial_operation_done(
        self,
        conn: Connection,
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
        conn.execute(query)
        return operation

    def mark_serial_operation_failed(
        self,
        conn: Connection,
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
        conn.execute(query)
        return operation
