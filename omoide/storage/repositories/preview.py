# -*- coding: utf-8 -*-
"""Preview repository.
"""
from omoide.domain import preview
from omoide.domain.interfaces import database
from omoide.storage.repositories import base
from omoide.storage.repositories import preview_sql


class PreviewRepository(
    base.BaseRepository,
    database.AbsPreviewRepository
):
    """Repository that performs all preview queries."""
    _query_get_item = preview_sql.GET_ITEM
    _query_get_neighbours = preview_sql.GET_NEIGHBOURS

    async def get_preview_item(
            self,
            item_uuid: str,
    ) -> preview.Item:
        """Return instance of item."""
        response = await self.db.fetch_one(
            query=self._query_get_item,
            values={
                'item_uuid': item_uuid,
            }
        )

        if response is None:
            return preview.Item.empty()
        return preview.Item.from_row(response)

    async def get_neighbours(self, item_uuid: str) -> list[str]:
        """Return uuids of all the neighbours."""
        response = await self.db.fetch_all(
            query=self._query_get_neighbours,
            values={
                'item_uuid': item_uuid,
            }
        )
        return [str(row['uuid']) for row in response]
