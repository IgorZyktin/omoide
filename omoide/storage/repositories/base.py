# -*- coding: utf-8 -*-
"""Base functionality for all concrete repositories.
"""
from typing import Optional, Any

from omoide.domain import auth, common
from omoide.domain.interfaces import repositories
from omoide.storage.repositories import base_sql


class BaseRepository(repositories.AbsRepository):
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

    async def get_location(
            self,
            item_uuid: str,
            details: common.Details,
    ) -> Optional[common.Location]:
        """Return Location of the item."""
        current_item = await self.get_item(item_uuid)

        if current_item is None:
            return None

        owner = await self.get_user(current_item.owner_uuid)

        if owner is None:
            return None

        ancestors = await self._get_ancestors(current_item, details)

        if ancestors:
            positioned_owner = await self.get_positioned_by_user(
                owner, ancestors[0].item, details)
        else:
            positioned_owner = await self.get_positioned_by_user(
                owner, current_item, details)

        return common.Location(
            owner=positioned_owner,
            items=ancestors,
            current_item=current_item,
        )

    async def _get_ancestors(
            self,
            item: common.Item,
            details: common.Details,
    ) -> list[common.PositionedItem]:
        """Return list of positioned ancestors of given item."""
        ancestors = []

        item_uuid = item.parent_uuid
        child_uuid = item.uuid

        while True:
            ancestor = await self.get_item_with_position(
                item_uuid=item_uuid,
                child_uuid=child_uuid,
                details=details,
            )

            if ancestor is None:
                break

            ancestors.append(ancestor)
            item_uuid = ancestor.item.parent_uuid
            child_uuid = ancestor.item.uuid

        ancestors.reverse()
        return ancestors

    async def user_is_public(
            self,
            owner_uuid: str,
    ) -> bool:
        """Return True if owner is a public user."""
        query = """
        SELECT 1 
        FROM public_users
        WHERE user_uuid = :user_uuid;
        """
        response = await self.db.fetch_one(query, {'user_uuid': owner_uuid})
        return response is not None

    async def get_positioned_by_user(
            self,
            user: auth.User,
            item: common.Item,
            details: common.Details,
    ) -> Optional[common.PositionedByUserItem]:
        """Return user with position information."""
        if await self.user_is_public(user.uuid):
            query = """
            WITH children AS (
                SELECT uuid
                FROM items
                WHERE owner_uuid = :owner_uuid
                  AND parent_uuid IS NULL
                ORDER BY number
            )
        SELECT (select array_position(array(select uuid from children),
                                      :item_uuid)) as position,
               (select count(*) from children) as total_items
        """
        else:
            raise

        values = {'owner_uuid': user.uuid, 'item_uuid': item.uuid}

        response = await self.db.fetch_one(query, values)

        if response is None:
            position = 1
            total_items = 1
        else:
            position = int(response['position'] or 1)
            total_items = int(response['total_items'] or 1)

        return common.PositionedByUserItem(
            user=user,
            position=position,
            total_items=total_items,
            items_per_page=details.items_per_page,
            item=item,
        )

    async def get_user(
            self,
            user_uuid: str,
    ) -> Optional[auth.User]:
        """Return user or None."""
        query = """
        SELECT *
        FROM users
        WHERE uuid = :user_uuid;
        """

        response = await self.db.fetch_one(query, {'user_uuid': user_uuid})
        return auth.User.from_map(response) if response else None

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
        return common.Item.from_map(response) if response else None

    async def get_item_with_position(
            self,
            item_uuid: str,
            child_uuid: str,
            details: common.Details,
    ) -> Optional[common.PositionedItem]:
        """Return item with its position in siblings."""
        query = """
        WITH children AS (
            SELECT uuid
            FROM items
            WHERE parent_uuid = :item_uuid
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
                                      :child_uuid)) as position,
               (select count(*) from children) as total_items
        FROM items
        WHERE uuid = :item_uuid;
        """

        values = {'item_uuid': item_uuid, 'child_uuid': child_uuid}
        response = await self.db.fetch_one(query, values)

        if response is None:
            return None

        mapping = dict(response)

        return common.PositionedItem(
            position=mapping.pop('position') or 1,
            total_items=mapping.pop('total_items') or 1,
            items_per_page=details.items_per_page,
            item=common.Item.from_map(mapping),
        )
