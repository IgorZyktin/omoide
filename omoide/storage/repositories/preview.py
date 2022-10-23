# -*- coding: utf-8 -*-
"""Preview repository.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base
from omoide.storage.repositories import rp_items


class PreviewRepository(
    rp_items.ItemsRepository,
    base.BaseRepository,
    interfaces.AbsPreviewRepository,
):
    """Repository that performs all preview queries."""

    async def get_neighbours(
            self,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours for given item UUID."""
        query = """
        SELECT uuid
        FROM items
        WHERE parent_uuid = (
            SELECT parent_uuid
            FROM items
            WHERE uuid = :item_uuid
        )
        ORDER BY number;
        """
        values = {
            'item_uuid': str(uuid),
        }

        response = await self.db.fetch_all(query, values)
        return [row['uuid'] for row in response]

    async def get_specific_neighbours(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours (which we have access to)."""
        query = """
        SELECT uuid
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE parent_uuid = (
            SELECT parent_uuid
            FROM items
            WHERE uuid = :item_uuid
        )
        AND (:user_uuid = ANY(cp.permissions)
             OR it.owner_uuid::text = :user_uuid)
        ORDER BY number;
        """

        values = {
            'user_uuid': str(user.uuid),
            'item_uuid': str(uuid),
        }

        response = await self.db.fetch_all(query, values)
        return [row['uuid'] for row in response]
