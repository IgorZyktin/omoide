# -*- coding: utf-8 -*-
"""Browse repository.
"""
from omoide.domain import browse, common
from omoide.domain.interfaces import database
from omoide.storage.repositories import base
from omoide.storage.repositories import browse_sql


class BrowseRepository(
    base.BaseRepository,
    database.AbsBrowseRepository
):
    """Repository that performs all browse queries."""
    _query_get_nested_items = browse_sql.GET_NESTED_ITEMS
    _query_count_nested_items = browse_sql.COUNT_NESTED_ITEMS

    async def get_nested_items(
            self,
            item_uuid: str,
            query: browse.Query,
    ) -> list[common.SimpleItem]:
        """Load all children and sub children of the record."""
        response = await self.db.fetch_all(
            query=self._query_get_nested_items,
            values={
                'item_uuid': item_uuid,
                'limit': query.items_per_page,
                'offset': (query.page - 1) * query.items_per_page,
            }
        )
        return [common.SimpleItem.from_row(x) for x in response]

    async def count_nested_items(
            self,
            item_uuid: str,
    ) -> int:
        """Count all children with all required fields."""
        response = await self.db.fetch_one(
            query=self._query_count_nested_items,
            values={
                'item_uuid': item_uuid,
            }
        )
        return int(response['total_items'])
