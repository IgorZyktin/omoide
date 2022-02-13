# -*- coding: utf-8 -*-
"""Browse repository.
"""
from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base


class BrowseRepository(
    base.BaseRepository,
    interfaces.AbsBrowseRepository,
):
    """Repository that performs all browse queries."""

    async def get_children(
            self,
            item_uuid: str,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Load all children and sub children of the record."""
        _query = """
        SELECT uuid,
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext
        FROM items
        WHERE parent_uuid = :item_uuid
        AND uuid <> :item_uuid
        ORDER BY number
        LIMIT :limit OFFSET :offset;
        """

        values = {
            'item_uuid': item_uuid,
            'limit': details.items_per_page,
            'offset': details.offset,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item.from_map(x) for x in response]

    async def count_items(
            self,
            item_uuid: str,
    ) -> int:
        """Count all children with all required fields."""
        query = """
        SELECT count(*) AS total_items
        FROM items
        WHERE parent_uuid = :item_uuid;
        """

        response = await self.db.fetch_one(query, {'item_uuid': item_uuid})
        return int(response['total_items'])
