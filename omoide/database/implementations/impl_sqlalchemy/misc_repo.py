"""Repository that performs various operations on different objects."""

from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import models
from omoide import utils
from omoide.database import db_models
from omoide.database.interfaces.abs_misc_repo import AbsMiscRepo


class MiscRepo(AbsMiscRepo[AsyncConnection]):
    """Repository that performs various operations on different objects."""

    async def create_serial_operation(
        self,
        conn: AsyncConnection,
        name: str,
        extras: dict[str, Any] | None = None,
    ) -> int:
        """Create serial operation."""
        stmt = (
            sa.insert(db_models.SerialOperation)
            .values(
                name=name,
                worker_name=None,
                status=models.OperationStatus.CREATED,
                extras=extras or {},
                created_at=utils.now(),
                updated_at=utils.now(),
                started_at=None,
                ended_at=None,
                log=None,
            )
            .returning(db_models.SerialOperation.id)
        )

        operation_id = (await conn.execute(stmt)).scalar()
        return operation_id if operation_id is not None else -1
