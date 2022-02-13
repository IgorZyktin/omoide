# -*- coding: utf-8 -*-
"""Base functionality for all concrete repositories.
"""
from typing import Optional

from omoide import domain
from omoide.storage.repositories import base_logic


class BaseRepository(base_logic.BaseRepositoryLogic):
    """Base functionality for all concrete repositories."""

    async def check_access(
            self,
            user: domain.User,
            item_uuid: str,
    ) -> domain.AccessStatus:
        """Check access to the item."""
        query = """
        SELECT owner_uuid,
               exists(SELECT 1
                      FROM public_users pu
                      WHERE pu.user_uuid = i.owner_uuid)  AS is_public,
               (SELECT :user_uuid = ANY (cp.permissions)) AS is_given
        FROM items i
                 LEFT JOIN computed_permissions cp ON cp.item_uuid = i.uuid
        WHERE uuid = :item_uuid;
        """

        values = {'user_uuid': user.uuid, 'item_uuid': item_uuid}
        response = await self.db.fetch_one(query, values)

        if response is None:
            return domain.AccessStatus.not_found()

        return domain.AccessStatus(
            exists=True,
            is_public=bool(response['is_public']),
            is_given=bool(response['is_given']),
        )

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
            user: domain.User,
            item: domain.Item,
            details: domain.Details,
    ) -> Optional[domain.PositionedByUserItem]:
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

        return domain.PositionedByUserItem(
            user=user,
            position=position,
            total_items=total_items,
            items_per_page=details.items_per_page,
            item=item,
        )

    async def get_user(
            self,
            user_uuid: str,
    ) -> Optional[domain.User]:
        """Return user or None."""
        query = """
        SELECT *
        FROM users
        WHERE uuid = :user_uuid;
        """

        response = await self.db.fetch_one(query, {'user_uuid': user_uuid})
        return domain.User.from_map(response) if response else None

    async def get_item(
            self,
            item_uuid: str,
    ) -> Optional[domain.Item]:
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
        return domain.Item.from_map(response) if response else None

    async def get_item_with_position(
            self,
            item_uuid: str,
            child_uuid: str,
            details: domain.Details,
    ) -> Optional[domain.PositionedItem]:
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

        return domain.PositionedItem(
            position=mapping.pop('position') or 1,
            total_items=mapping.pop('total_items') or 1,
            items_per_page=details.items_per_page,
            item=domain.Item.from_map(mapping),
        )
