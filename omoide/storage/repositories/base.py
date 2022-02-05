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
    ) -> list[common.PositionedItem]:
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
        WHERE uuid = :item_uuid;
        """

        response = await self.db.fetch_one(query, {'item_uuid': item_uuid})

        if response is None:
            return None

        return common.Item.from_map(response)

    async def get_item_with_position(
            self,
            current_item: common.Item,
    ) -> Optional[common.PositionedItem]:
        """Return item with its position in siblings."""
        query = """
        WITH children AS (
            SELECT uuid
            FROM items
            WHERE parent_uuid = :parent_uuid
            ORDER BY number
        )
        SELECT uuid, 
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext,
               (select array_position(array(select uuid from children),
                                      :item_uuid)) as position,
               (select count(*) from children) as total
        FROM items
        WHERE uuid = :item_uuid
        """

        values = {
            'item_uuid': current_item.uuid,
            'parent_uuid': current_item.parent_uuid,
        }

        response = await self.db.fetch_one(query, values)

        if response is None:
            return None

        print(dict(response))
