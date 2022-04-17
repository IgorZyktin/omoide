# -*- coding: utf-8 -*-
"""Preview repository.
"""
from typing import Optional

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base


class PreviewRepository(
    base.BaseRepository,
    interfaces.AbsPreviewRepository,
):
    """Repository that performs all preview queries."""

    async def get_extended_item(
            self,
            item_uuid: str,
    ) -> Optional[domain.ExtendedItem]:
        """Return instance of item."""
        query = """
        SELECT *
        FROM items
        WHERE uuid = :item_uuid;
        """

        response = await self.db.fetch_one(query, {'item_uuid': item_uuid})
        return domain.ExtendedItem.from_map(response) if response else None

    async def get_neighbours(self, item_uuid: str) -> list[str]:
        """Return uuids of all the neighbours."""
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

        response = await self.db.fetch_all(query, {'item_uuid': item_uuid})
        return [str(row['uuid']) for row in response]

    async def get_specific_neighbours(
            self,
            user: domain.User,
            item_uuid: str,
    ) -> list[str]:
        """Return uuids of all the neighbours (which we have access to)."""
        query = """
        SELECT uuid
        FROM items it
            RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
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
            'user_uuid': user.uuid,
            'item_uuid': item_uuid,
        }

        response = await self.db.fetch_all(query, values)
        return [str(row['uuid']) for row in response]
