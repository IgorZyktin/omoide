"""Preview repository."""
from uuid import UUID

import sqlalchemy as sa

from omoide import models
from omoide.domain import interfaces
from omoide.storage.database import models as db_models
from omoide.storage.repositories.asyncpg import queries
from omoide.storage.repositories.asyncpg.rp_browse import BrowseRepository


class PreviewRepository(
    interfaces.AbsPreviewRepository,
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
