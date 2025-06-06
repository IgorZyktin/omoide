"""Repository that performs various operations on different objects."""

from typing import Any

import python_utilz as pu
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
        name: str,
        extras: dict[str, Any],
        payload: bytes = b'',
    ) -> int:
        """Create serial operation."""
        now = pu.now()

        stmt = (
            sa.insert(db_models.SerialOperation)
            .values(
                name=name,
                status=operations.OperationStatus.CREATED.value,
                extras=extras,
                created_at=now,
                updated_at=now,
                started_at=None,
                ended_at=None,
                log='',
                payload=payload,
                processed_by=[],
            )
            .returning(db_models.SerialOperation.id)
        )

        operation_id = (await conn.execute(stmt)).scalar()
        return operation_id if operation_id is not None else -1

    async def create_parallel_operation(
        self,
        conn: AsyncConnection,
        name: str,
        extras: dict[str, Any],
        payload: bytes = b'',
    ) -> int:
        """Create parallel operation."""
        now = pu.now()

        stmt = (
            sa.insert(db_models.ParallelOperation)
            .values(
                name=name,
                status=operations.OperationStatus.CREATED,
                extras=extras,
                created_at=now,
                updated_at=now,
                started_at=None,
                ended_at=None,
                log='',
                payload=payload,
                processed_by=[],
            )
            .returning(db_models.ParallelOperation.id)
        )

        operation_id = (await conn.execute(stmt)).scalar()
        return operation_id if operation_id is not None else -1
