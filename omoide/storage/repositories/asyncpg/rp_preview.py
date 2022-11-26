# -*- coding: utf-8 -*-
"""Preview repository.
"""
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg import queries
from omoide.storage.repositories.asyncpg.rp_browse import BrowseRepository


class PreviewRepository(
    interfaces.AbsPreviewRepository,
    BrowseRepository,
):
    """Repository that performs all preview queries."""

    async def get_neighbours(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours for given item UUID."""
        stmt = sa.select(
            models.Item.uuid
        )

        if user.is_anon():
            stmt = stmt.join(
                models.User,
                models.Item.owner_uuid == models.User.uuid
            ).where(
                models.User.uuid.in_(queries.public_user_uuids())
            )
        else:
            stmt = stmt.join(
                models.ComputedPermissions,
                models.ComputedPermissions.item_uuid == models.Item.uuid,
            ).where(
                sa.or_(
                    models.Item.owner_uuid == str(user.uuid),
                    models.ComputedPermissions.permissions.any(str(user.uuid)),
                )
            )

        stmt = stmt.where(
            models.Item.parent_uuid == sa.select(
                models.Item.parent_uuid
            ).where(
                models.Item.uuid == str(uuid)
            ).scalar_subquery()
        ).order_by(
            models.Item.number
        )

        response = await self.db.fetch_all(stmt)
        return [row['uuid'] for row in response]
