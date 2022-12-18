# -*- coding: utf-8 -*-
"""Repository that performs basic read operations on items.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg import queries


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
                      WHERE pu.user_uuid = owner_uuid) AS is_public,
               (SELECT :user_uuid = ANY (permissions)) AS is_permitted,
               owner_uuid::text = :user_uuid AS is_owner
        FROM items
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

    async def count_all_children_of(
            self,
            item: domain.Item,
    ) -> int:
        """Count dependant items."""
        stmt = """
        WITH RECURSIVE nested_items AS (
            SELECT parent_uuid,
                   uuid
            FROM items
            WHERE uuid = :uuid
            UNION ALL
            SELECT i.parent_uuid,
                   i.uuid
            FROM items i
                     INNER JOIN nested_items it2 ON i.parent_uuid = it2.uuid
        )
        SELECT count(*) AS total
        FROM nested_items;
        """

        response = await self.db.fetch_one(stmt, {'uuid': item.uuid})

        if response is None:
            return 0

        return response['total']

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

    async def read_children_of(
            self,
            user: domain.User,
            item: domain.Item,
            ignore_collections: bool,
    ) -> list[domain.Item]:
        """Return all direct descendants of the given item."""
        stmt = sa.select(
            models.Item
        ).where(
            models.Item.parent_uuid == item.uuid,
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        if ignore_collections:
            stmt = stmt.where(
                models.Item.is_collection == False,  # noqa
            )

        stmt = stmt.order_by(
            models.Item.number
        )

        response = await self.db.fetch_all(stmt)
        return [domain.Item(**each) for each in response]

    async def get_simple_location(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
    ) -> Optional[domain.SimpleLocation]:
        """Return Location of the item (without pagination)."""
        ancestors = await self.get_simple_ancestors(user, item)
        return domain.SimpleLocation(items=ancestors + [item])

    async def get_simple_ancestors(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> list[domain.Item]:
        """Return list of ancestors for given item."""
        assert user
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
            user: domain.User,
    ) -> int:
        """Return total amount of items for given user uuid."""
        assert user.is_registered
        stmt = sa.select(
            sa.func.count().label('total_items')
        ).select_from(
            models.Item
        ).where(
            models.Item.owner_uuid == user.uuid
        )
        response = await self.db.fetch_one(stmt)
        return int(response['total_items'])

    async def get_all_parent_uuids(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> list[UUID]:
        """Return all parents of given item."""
        stmt = """
        WITH RECURSIVE parents AS (
            SELECT parent_uuid,
                   uuid,
                   name
            FROM items
            WHERE uuid = :uuid
            UNION
            SELECT i.parent_uuid,
                   i.uuid,
                   i.name
            FROM items i
                     INNER JOIN parents ON i.uuid = parents.parent_uuid
        )
        SELECT parent_uuid FROM parents WHERE parent_uuid IS NOT NULL;
        """

        values = {
            'uuid': str(item.uuid),
        }

        response = await self.db.fetch_all(stmt, values)
        return [x['uuid'] for x in response]
