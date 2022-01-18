# -*- coding: utf-8 -*-
"""Preview repository.
"""
from omoide.domain import preview, auth
from omoide.domain.interfaces import database
from omoide.storage.repositories import preview_sql


class PreviewRepository(database.AbsPreviewRepository):
    """Repository that performs all preview queries."""
    _q_access = preview_sql.CHECK_ACCESS
    _q_item = preview_sql.GET_EXTENDED_ITEM
    _q_neighbours = preview_sql.GET_NEIGHBOURS

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    async def get_item_or_empty(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> tuple[preview.Item, list[str], preview.AccessStatus]:
        """Load item with all required fields or return failure."""
        async with self.db.transaction():
            status = await self._check_access(user, item_uuid)

            if status.is_not_given:
                item = preview.Item.empty()
            else:
                item = await self._get_item(item_uuid)
                neighbours = await self._get_neighbours(item_uuid)

        return item, neighbours, status

    async def _check_access(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> preview.AccessStatus:
        """Check access to the item."""
        response = await self.db.fetch_one(
            query=self._q_access,
            values={'user_uuid': user.uuid, 'item_uuid': item_uuid}
        )

        if response is None:
            return preview.AccessStatus(
                exists=False,
                is_public=False,
                is_given=False,
            )

        return preview.AccessStatus(
            exists=True,
            is_public=bool(response['is_public']),
            is_given=bool(response['is_given']),
        )

    @staticmethod
    def _cast_item(row) -> preview.Item:
        """Convert row into item model."""
        source = dict(row)
        source['uuid'] = str(source['uuid'])
        source['parent_uuid'] = (str(source['parent_uuid'])
                                 if source['parent_uuid'] else None)
        source['owner_uuid'] = (str(source['owner_uuid'])
                                if source['owner_uuid'] else None)
        source['groups'] = source.pop('permissions')

        return preview.Item(**source)

    async def _get_item(
            self,
            item_uuid: str,
    ) -> preview.Item:
        """Check access to the item."""
        response = await self.db.fetch_one(
            query=self._q_item,
            values={'item_uuid': item_uuid}
        )

        if response is None:
            return preview.Item.empty()
        return self._cast_item(response)

    async def _get_neighbours(self, item_uuid: str) -> list[str]:
        """Load all siblings on an item."""
        # TODO(i.zyktin): replace with simple item model
        response = await self.db.fetch_all(
            query=self._q_neighbours,
            values={'item_uuid': item_uuid}
        )
        return [str(row['uuid']) for row in response]
