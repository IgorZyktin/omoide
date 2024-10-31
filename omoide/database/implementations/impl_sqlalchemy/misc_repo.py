"""Repository that performs various operations on different objects."""

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_misc_repo import AbsMiscRepo
from omoide.serial_operations import SerialOperation


class MiscRepo(AbsMiscRepo[AsyncConnection]):
    """Repository that performs various operations on different objects."""

    async def get_computed_tags(self, conn: AsyncConnection, item: models.Item) -> set[str]:
        """Get computed tags for this item."""
        stmt = sa.select(db_models.ComputedTags.tags).where(
            db_models.ComputedTags.item_id == item.id
        )
        response = (await conn.execute(stmt)).fetchone()
        return {str(row) for row in response.tags}

    async def create_serial_operation(
        self,
        conn: AsyncConnection,
        operation: SerialOperation,
    ) -> int:
        """Create serial operation."""
        stmt = (
            sa.insert(db_models.SerialOperation)
            .values(
                name=operation.name,
                worker_name=operation.worker_name,
                status=operation.status,
                extras=operation.extras,
                created_at=operation.created_at,
                updated_at=operation.updated_at,
                started_at=operation.started_at,
                ended_at=operation.ended_at,
                log=operation.log,
            )
            .returning(db_models.SerialOperation.id)
        )

        operation_id = int((await conn.execute(stmt)).scalar())
        operation.id = operation_id
        return operation_id
