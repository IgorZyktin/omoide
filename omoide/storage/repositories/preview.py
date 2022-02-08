# -*- coding: utf-8 -*-
"""Preview repository.
"""
from typing import Optional

from omoide.domain import preview
from omoide.domain.interfaces import repositories
from omoide.storage.repositories import base


class PreviewRepository(
    base.BaseRepository,
    repositories.AbsPreviewRepository,
):
    """Repository that performs all preview queries."""

    async def get_extended_item(
            self,
            item_uuid: str,
    ) -> Optional[preview.ExtendedItem]:
        """Return instance of item."""
        query = """
        SELECT *
        FROM items
        WHERE uuid = :item_uuid;
        """

        response = await self.db.fetch_one(query, {'item_uuid': item_uuid})
        return preview.ExtendedItem.from_map(response) if response else None

    async def get_neighbours(self, item_uuid: str) -> list[str]:
        """Return uuids of all the neighbours."""
        query = """
        SELECT uuid
        FROM items
        WHERE parent_uuid = (
            SELECT parent_uuid
            FROM items
            WHERE uuid = :item_uuid
        );
        """

        response = await self.db.fetch_all(query, {'item_uuid': item_uuid})
        return [str(row['uuid']) for row in response]
