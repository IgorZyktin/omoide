# -*- coding: utf-8 -*-
"""Preview repository.
"""
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg.rp_browse import BrowseRepository


class PreviewRepository(
    interfaces.AbsPreviewRepository,
    BrowseRepository,
):
    """Repository that performs all preview queries."""

    async def get_neighbours_anon(
            self,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours for given item UUID."""
        stmt = sa.select(
            models.Item.uuid
        ).where(
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

    async def get_neighbours_known(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours (which we have access to)."""
        stmt = sa.select(
            models.Item.uuid
        ).join(
            models.ComputedPermissions,
            models.ComputedPermissions.item_uuid == models.Item.uuid,
        ).where(
            models.Item.parent_uuid == sa.select(
                models.Item.parent_uuid
            ).where(
                models.Item.uuid == str(uuid)
            ).scalar_subquery(),
            sa.or_(
                str(user.uuid) == sa.any_(
                    models.ComputedPermissions.permissions
                ),
                models.Item.owner_uuid == str(user.uuid),
            )
        ).order_by(
            models.Item.number
        )
        response = await self.db.fetch_all(stmt)
        return [row['uuid'] for row in response]
