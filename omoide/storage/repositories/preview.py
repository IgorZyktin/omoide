# -*- coding: utf-8 -*-
"""Preview repository.
"""
from typing import Optional
from uuid import UUID

from omoide import domain, utils
from omoide.domain import interfaces
from omoide.storage.repositories import base, rp_items


class PreviewRepository(
    rp_items.ItemsRepository,
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
        if response is not None:
            # FIXME: refactor this
            item = domain.ExtendedItem.from_map(response)
            query_for_tags = """
            SELECT tags
            FROM computed_tags
            WHERE item_uuid = :item_uuid;
            """
            all_tags = await self.db.fetch_one(query_for_tags,
                                               {'item_uuid': item_uuid})
            tags = [
                tag
                for tag in all_tags['tags']
                if all((
                    not tag.endswith('jpg'),
                    not utils.is_valid_uuid(tag),
                ))
            ]
            item.tags = tags
            return item
        return None

    async def get_neighbours(self, item_uuid: str) -> list[UUID]:
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
        return [row['uuid'] for row in response]

    async def get_specific_neighbours(
            self,
            user: domain.User,
            item_uuid: str,
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
            'item_uuid': item_uuid,
        }

        response = await self.db.fetch_all(query, values)
        return [row['uuid'] for row in response]
