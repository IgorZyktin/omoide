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

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    async def get_item_or_empty(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> tuple[preview.Item, preview.AccessStatus]:
        """Load item with all required fields or return failure."""
        async with self.db.transaction():
            status = await self._check_access(user, item_uuid)

            if status.is_not_given:
                item = preview.Item.empty()
            else:
                item = await self._get_item(item_uuid)

        return item, status

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

        source = dict(response)
        source['uuid'] = str(source['uuid'])
        source['parent_uuid'] = (str(source['parent_uuid'])
                                 if source['parent_uuid'] else None)
        source['owner_uuid'] = (str(source['owner_uuid'])
                                if source['owner_uuid'] else None)
        source['groups'] = source.pop('permissions')

        return preview.Item(**source)