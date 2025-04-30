"""Repository that performs various operations on different objects."""

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import operations
from omoide.database import db_models
from omoide.database.interfaces.abs_misc_repo import AbsMiscRepo


class MiscRepo(AbsMiscRepo[AsyncConnection]):
    """Repository that performs various operations on different objects."""

    async def create_serial_operation(
        self,
        conn: AsyncConnection,
        operation: operations.BaseSerialOperation,
    ) -> int:
        """Create serial operation."""
        stmt = (
            sa.insert(db_models.SerialOperation)
            .values(
                name=operation.name,
                worker_name=operation.worker_name,
                status=operations.OperationStatus.CREATED,
                extras=operation.dump_extras(),
                created_at=operation.created_at,
                updated_at=operation.updated_at,
                started_at=operation.started_at,
                ended_at=operation.ended_at,
                log=operation.log,
                payload=operation.payload,
            )
            .returning(db_models.SerialOperation.id)
        )

        operation_id = (await conn.execute(stmt)).scalar()
        return operation_id if operation_id is not None else -1

    async def create_parallel_operation(
        self,
        conn: AsyncConnection,
        operation: operations.BaseParallelOperation,
    ) -> int:
        """Create parallel operation."""
        stmt = (
            sa.insert(db_models.ParallelOperation)
            .values(
                name=operation.name,
                status=operations.OperationStatus.CREATED,
                extras=operation.dump_extras(),
                created_at=operation.created_at,
                updated_at=operation.updated_at,
                started_at=operation.started_at,
                ended_at=operation.ended_at,
                log=operation.log,
                payload=operation.payload,
                processed_by=operation.processed_by,
            )
            .returning(db_models.ParallelOperation.id)
        )

        operation_id = (await conn.execute(stmt)).scalar()
        return operation_id if operation_id is not None else -1
