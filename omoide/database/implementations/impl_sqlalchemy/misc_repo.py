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

        operation_id = int((await conn.execute(stmt)).scalar())
        return operation_id
