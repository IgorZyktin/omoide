# -*- coding: utf-8 -*-
"""Repository that performs basic read operations on items.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models


class ItemsReadRepository(interfaces.AbsItemsReadRepository):
    """Repository that performs basic read operations on items."""

    async def check_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Check access to the Item with given UUID for the given User."""
        query = """
        SELECT owner_uuid,
               exists(SELECT 1
                      FROM public_users pu
                      WHERE pu.user_uuid = i.owner_uuid)  AS is_public,
               (SELECT :user_uuid = ANY (cp.permissions)) AS is_permitted,
               owner_uuid::text = :user_uuid AS is_owner
        FROM items i
                 LEFT JOIN computed_permissions cp ON cp.item_uuid = i.uuid
        WHERE uuid = :uuid;
        """

        values = {
            'user_uuid': str(user.uuid),
            'uuid': str(uuid),
        }
        response = await self.db.fetch_one(query, values)

        if response is None:
            return domain.AccessStatus.not_found()

        return domain.AccessStatus(
            exists=True,
            is_public=bool(response['is_public']),
            is_permitted=bool(response['is_permitted']),
            is_owner=bool(response['is_owner']),
        )

    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return item or None."""
        stmt = sa.select(
            models.Item
        ).where(
            models.Item.uuid == uuid
        )

        response = await self.db.fetch_one(stmt)

        return domain.Item(**response) if response else None

    async def read_children(
            self,
            uuid: UUID,
    ) -> list[domain.Item]:
        """Return all direct descendants of the given item."""
        stmt = """
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
        WHERE parent_uuid = :uuid;
        """

        response = await self.db.fetch_all(stmt, {'uuid': str(uuid)})
        return [domain.Item(**each) for each in response]

    async def get_simple_location(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
    ) -> Optional[domain.SimpleLocation]:
        """Return Location of the item (without pagination)."""
        ancestors = await self.get_simple_ancestors(item)
        return domain.SimpleLocation(items=ancestors + [item])

    async def get_simple_ancestors(
            self,
            item: domain.Item,
    ) -> list[domain.Item]:
        """Return list of ancestors for given item."""
        # TODO(i.zyktin): what if user has no access
        #  to the item in the middle of dependence chain?

        ancestors = []
        item_uuid = item.parent_uuid

        while True:
            if item_uuid is None:
                break

            ancestor = await self.read_item(item_uuid)

            if ancestor is None:
                break

            ancestors.append(ancestor)
            item_uuid = ancestor.parent_uuid

        ancestors.reverse()
        return ancestors

    async def count_items_by_owner(
            self,
            uuid: UUID,
    ) -> int:
        """Return total amount of items for given user uuid."""
        stmt = sa.select(
            sa.func.count().label('total_items')
        ).select_from(
            models.Item
        ).where(
            models.Item.owner_uuid == uuid
        )
        response = await self.db.fetch_one(stmt)
        return int(response['total_items'])
