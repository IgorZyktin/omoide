# -*- coding: utf-8 -*-
"""Repository that show items at the home endpoint.
"""
import sqlalchemy
from sqlalchemy import func

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models
from omoide.storage.repositories import base


class HomeRepository(
    base.BaseRepository,
    interfaces.AbsHomeRepository,
):
    """Repository that show items at the home endpoint."""

    async def find_home_items_for_anon(
            self,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find home items for unauthorised user."""
        subquery = sqlalchemy.select(models.PublicUsers.user_uuid)
        conditions = [
            models.Item.owner_uuid.in_(subquery)
        ]

        if aim.nested:
            conditions.append(models.Item.parent_uuid == None)

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
            stmt = stmt.order_by(models.Item.number)
        else:
            stmt = stmt.order_by(func.random())

        stmt = stmt.limit(aim.items_per_page)

        response = await self.db.fetch_all(stmt)
        # TODO - damn asyncpg tries to bee too smart
        items = [
            domain.Item.from_map(dict(zip(row.keys(), row.values())))
            for row in response
        ]
        return items

    async def select_home_random_nested_known(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find random nested items for authorised user."""
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
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE (:user_uuid = ANY(cp.permissions)
               OR it.owner_uuid::text = :user_uuid)
               AND parent_uuid IS NULL
        ORDER BY random() LIMIT :limit;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': aim.items_per_page,
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_ordered_nested_known(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find ordered nested items for authorised user."""
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
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE (:user_uuid = ANY(cp.permissions)
               OR it.owner_uuid::text = :user_uuid)
               AND parent_uuid IS NULL
               AND number > :last_seen
        ORDER BY number LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': aim.items_per_page,
            'last_seen': aim.last_seen,
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_random_flat_known(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find random flat items for authorised user."""
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
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE (:user_uuid = ANY(cp.permissions)
               OR it.owner_uuid::text = :user_uuid)
        ORDER BY random() LIMIT :limit;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': aim.items_per_page,
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_ordered_flat_known(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find ordered flat items for authorised user."""
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
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE (:user_uuid = ANY(cp.permissions)
               OR it.owner_uuid::text = :user_uuid)
               AND number > :last_seen
        ORDER BY number LIMIT :limit;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': aim.items_per_page,
            'last_seen': aim.last_seen,
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]
