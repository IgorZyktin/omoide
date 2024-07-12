"""Preview repository."""
from uuid import UUID

import sqlalchemy as sa

from omoide import models
from omoide.storage.database import db_models
from omoide.storage.implementations.asyncpg import BrowseRepository
from omoide.storage.implementations.asyncpg.repositories import queries
from omoide.storage import interfaces as storage_interfaces


class PreviewRepository(
    storage_interfaces.AbsPreviewRepository,
    BrowseRepository,
):
    """Repository that performs all preview queries."""

    async def get_neighbours(
            self,
            user: models.User,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours for given item UUID."""
        stmt = sa.select(
            db_models.Item.uuid
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        stmt = stmt.where(
            db_models.Item.parent_uuid == sa.select(
                db_models.Item.parent_uuid
            ).where(
                db_models.Item.uuid == str(uuid)
            ).scalar_subquery()
        ).order_by(
            db_models.Item.number
        )

        response = await self.db.fetch_all(stmt)
        return [row['uuid'] for row in response]
