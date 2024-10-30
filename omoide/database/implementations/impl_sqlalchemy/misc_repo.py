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

    # async def update_computed_tags(
    #     self,
    #     conn: AsyncConnection,
    #     item: models.Item,
    #     parent_computed_tags: set[str],
    # ) -> set[str]:
    #     """Update computed tags for this item."""
    #     computed_tags = item.get_computed_tags(parent_computed_tags)
    #
    #     insert = pg_insert(db_models.ComputedTags).values(
    #         item_uuid=item.uuid,
    #         tags=tuple(computed_tags),
    #     )
    #
    #     stmt = insert.on_conflict_do_update(
    #         index_elements=[db_models.ComputedTags.item_uuid],
    #         set_={'tags': insert.excluded.tags},
    #     )
    #
    #     await self.db.execute(stmt)
    #     return computed_tags

    # async def drop_unused_known_tags_anon(self) -> None:
    #     """Drop tags with counter less of equal to 0."""
    #     stmt = sa.delete(db_models.KnownTagsAnon).where(
    #         db_models.KnownTagsAnon.counter <= 0,
    #     )
    #     await self.db.execute(stmt)

    # async def drop_unused_known_tags_known(self, user: models.User) -> None:
    #     """Drop tags with counter less of equal to 0."""
    #     stmt = sa.delete(db_models.KnownTags).where(
    #         db_models.KnownTags.user_id == user.id,
    #         db_models.KnownTags.counter <= 0,
    #     )
    #     await self.db.execute(stmt)

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
