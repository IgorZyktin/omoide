# -*- coding: utf-8 -*-
"""Browse repository.
"""
from uuid import UUID

import sqlalchemy
from sqlalchemy import desc, func

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models
from omoide.storage.repositories import base
from omoide.storage.repositories import items


class BrowseRepository(
    items.ItemsRepository,
    base.BaseRepository,
    interfaces.AbsBrowseRepository,
):
    """Repository that performs all browse queries."""

    async def get_children(
            self,
            item_uuid: str,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Load all children and sub children of the record."""
        _query = """
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
        WHERE parent_uuid = :item_uuid
        AND uuid <> :item_uuid
        ORDER BY number
        LIMIT :limit OFFSET :offset;
        """

        values = {
            'item_uuid': item_uuid,
            'limit': details.items_per_page,
            'offset': details.offset,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item.from_map(x) for x in response]

    async def count_items(
            self,
            item_uuid: str,
    ) -> int:
        """Count all children with all required fields."""
        query = """
        SELECT count(*) AS total_items
        FROM items
        WHERE parent_uuid = :item_uuid;
        """

        response = await self.db.fetch_one(query, {'item_uuid': item_uuid})
        return int(response['total_items'])

    async def get_specific_children(
            self,
            user: domain.User,
            item_uuid: str,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Load all children with all required fields (and access)."""
        _query = """
        SELECT uuid,
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE parent_uuid = :item_uuid
            AND uuid <> :item_uuid
            AND (:user_uuid = ANY(cp.permissions)
                 OR it.owner_uuid::text = :user_uuid)
        ORDER BY number
        LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': user.uuid,
            'item_uuid': item_uuid,
            'limit': details.items_per_page,
            'offset': details.offset,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item.from_map(x) for x in response]

    async def count_specific_items(
            self,
            user: domain.User,
            item_uuid: str,
    ) -> int:
        """Count all children with all required fields (and access)."""
        query = """
        SELECT count(*) AS total_items
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE parent_uuid = :item_uuid
            AND (:user_uuid = ANY(cp.permissions)
                 OR it.owner_uuid::text = :user_uuid);
        """

        values = {
            'user_uuid': user.uuid,
            'item_uuid': item_uuid,
        }

        response = await self.db.fetch_one(query, values)
        return int(response['total_items'])

    async def dynamic_children_for_anon(
            self,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Load all children for given UUID (for Anon)."""
        subquery = sqlalchemy.select(models.PublicUsers.user_uuid)
        conditions = [
            models.Item.parent_uuid == uuid,
            models.Item.owner_uuid.in_(subquery)  # noqa
        ]

        if aim.nested:
            conditions.append(models.Item.parent_uuid == uuid)  # noqa

        if aim.ordered:
            conditions.append(models.Item.number > aim.last_seen)

        stmt = sqlalchemy.select(
            models.Item.uuid,
            models.Item.parent_uuid,
            models.Item.owner_uuid,
            models.Item.number,
            models.Item.name,
            models.Item.is_collection,
            models.Item.content_ext,
            models.Item.preview_ext,
            models.Item.thumbnail_ext,
        ).where(*conditions)

        if aim.ordered:
            stmt = stmt.order_by(
                desc(models.Item.is_collection),
                models.Item.number,
            )
        else:
            stmt = stmt.order_by(func.random())

        stmt = stmt.limit(aim.items_per_page)

        response = await self.db.fetch_all(stmt)
        # TODO - damn asyncpg tries to bee too smart
        _items = [
            domain.Item.from_map(dict(zip(row.keys(), row.values())))
            for row in response
        ]
        return _items

    async def dynamic_children_for_known(
            self,
            user: domain.User,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Load all children for given UUID (for known user)."""
        conditions = [
            sqlalchemy.or_(
                models.Item.owner_uuid == user.uuid,
                models.ComputedPermissions.permissions.any(user.uuid),
            )
        ]

        # TODO(i.zyktin): add recursive call here
        # if aim.nested:
        if 1 == 1:
            conditions.append(models.Item.parent_uuid == uuid)  # noqa

        if aim.ordered:
            conditions.append(models.Item.number > aim.last_seen)

        stmt = sqlalchemy.select(
            models.Item.uuid,
            models.Item.parent_uuid,
            models.Item.owner_uuid,
            models.Item.number,
            models.Item.name,
            models.Item.is_collection,
            models.Item.content_ext,
            models.Item.preview_ext,
            models.Item.thumbnail_ext,
        ).select_from(
            models.Item.__table__.join(
                models.ComputedPermissions,
                models.Item.uuid == models.ComputedPermissions.item_uuid,
                isouter=True,
            )
        ).where(*conditions)

        if aim.ordered:
            stmt = stmt.order_by(
                desc(models.Item.is_collection),
                models.Item.number,
            )
        else:
            stmt = stmt.order_by(func.random())

        stmt = stmt.limit(aim.items_per_page)

        response = await self.db.fetch_all(stmt)
        # TODO - damn asyncpg tries to bee too smart
        _items = [
            domain.Item.from_map(dict(zip(row.keys(), row.values())))
            for row in response
        ]
        return _items
