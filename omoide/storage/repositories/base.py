# -*- coding: utf-8 -*-
"""Base functionality for all concrete repositories.
"""
from typing import Optional, Any

from omoide.domain import auth, common
from omoide.domain.interfaces import database
from omoide.storage.repositories import base_sql


class BaseRepository(database.AbsRepository):
    """Base functionality for all concrete repositories."""
    _query_check_access = base_sql.CHECK_ACCESS
    _query_get_ancestors = base_sql.GET_ANCESTORS
    _query_get_owner = base_sql.GET_OWNER

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:
        """Start transaction."""
        return self.db.transaction()

    async def check_access(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> common.AccessStatus:
        """Check access to the item."""
        response = await self.db.fetch_one(
            query=self._query_check_access,
            values={
                'user_uuid': user.uuid,
                'item_uuid': item_uuid,
            }
        )

        if response is None:
            return common.AccessStatus.not_found()

        return common.AccessStatus(
            exists=True,
            is_public=bool(response['is_public']),
            is_given=bool(response['is_given']),
        )

    async def get_location(self, item_uuid: str) -> common.Location:
        """Return Location of the item."""
        current_item = await self.get_item(item_uuid)

        if current_item is None:
            return common.Location.empty()

        owner = await self.get_user(current_item.owner_uuid)

        if owner is None:
            return common.Location.empty()

        ancestors = await self.get_item_with_position(current_item)

        # ancestors_response = await self.db.fetch_all(
        #     query=self._query_get_ancestors,
        #     values={
        #         'item_uuid': item_uuid,
        #     }
        # )
        #
        # if ancestors_response is None or not ancestors_response:
        #     return common.Location.empty()
        #
        # items = [common.SimpleItem.from_row(x) for x in ancestors_response]
        #
        # pos = await self.get_item_with_position(item_uuid)
        #
        # parent_response = await self.db.fetch_one(
        #     query=self._query_get_owner,
        #     values={
        #         'user_uuid': items[-1].owner_uuid,
        #     }
        # )
        #
        # if parent_response is None:
        #     return common.Location.empty()
        #
        # items.reverse()
        #
        # return common.Location(
        #     owner=common.SimpleUser.from_row(parent_response),
        #     items=items,
        # )

    async def _get_ancestors(
            self,
            current_item: common.Item,
    ) -> list[common.SimplePositionedItem]:
        """Return list of positioned ancestors."""
        ancestors = []

        # parent = await self.get_item_with_position(current_item.)
        ancestors.reverse()
        return ancestors

    async def get_user(
            self,
            user_uuid: str,
    ) -> Optional[common.SimpleUser]:
        """Return user or None."""
        query = """
        SELECT uuid,
               name
        FROM users
        WHERE uuid = :user_uuid;
        """

        response = await self.db.fetch_one(query, {'user_uuid': user_uuid})

        if response is None:
            return None

        return common.SimpleUser.from_row(response)

    async def get_item(
            self,
            item_uuid: str,
    ) -> Optional[common.Item]:
        """Return item or None."""
        query = """
        SELECT parent_uuid,
               owner_uuid,
               uuid,
               is_collection,
               name,
               thumbnail_ext
        FROM items
        WHERE uuid = :item_uuid;
        """

        response = await self.db.fetch_one(query, {'item_uuid': item_uuid})

        if response is None:
            return None

        return common.Item.from_map(response)

    async def get_item_with_position(
            self,
            item_uuid: str,
    ) -> Optional[common.SimplePositionedItem]:
        """Return item with its position in siblings."""
        query = """
WITH children AS (
    SELECT uuid
    FROM items
    WHERE parent_uuid = '6302fbc8-de32-4db5-83eb-0fc283cecd9e'
    ORDER BY number
)
SELECT parent_uuid,
       owner_uuid,
       uuid,
       is_collection,
       name,
       thumbnail_ext,
       (select array_position(array(select uuid from children),
                              '52d42a9a-2bee-4751-9868-af29fd91f5a6')) as position,
       (select count(*) from children)                                 as total
FROM items
WHERE uuid = '6302fbc8-de32-4db5-83eb-0fc283cecd9e'

        """

        values = {'item_uuid': item_uuid}

        response = await self.db.fetch_one(query, values)

        if response is None:
            return None

        print(dict(response))
