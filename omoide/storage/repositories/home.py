# -*- coding: utf-8 -*-
"""Repository that show items at the home endpoint.
"""
from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base


class HomeRepository(
    base.BaseRepository,
    interfaces.AbsHomeRepository,
):
    """Repository that show items at the home endpoint."""

    async def select_home_random_nested_anon(
            self,
    ) -> list[domain.Item]:
        """Find random nested items for unauthorised user."""
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
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
            AND parent_uuid is NULL
        ORDER BY random() LIMIT :limit OFFSET :offset;
        """

        values = {
            'limit': 10,  # FIXME
            'offset': 0,  # FIXME
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_ordered_nested_anon(
            self,
    ) -> list[domain.Item]:
        """Find ordered nested items for unauthorised user."""
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
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
            AND parent_uuid is NULL
        ORDER BY number LIMIT :limit OFFSET :offset;
        """

        values = {
            'limit': 10,  # FIXME
            'offset': 0,  # FIXME
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_random_flat_anon(
            self,
    ) -> list[domain.Item]:
        """Find random flat items for unauthorised user."""
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
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
        ORDER BY random() LIMIT :limit OFFSET :offset;
        """

        values = {
            'limit': 10,  # FIXME
            'offset': 0,  # FIXME
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_ordered_flat_anon(
            self,
    ) -> list[domain.Item]:
        """Find ordered flat items for unauthorised user."""
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
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
        ORDER BY number LIMIT :limit OFFSET :offset;
        """

        values = {
            'limit': 10,  # FIXME
            'offset': 0,  # FIXME
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_random_nested_known(
            self,
            user: domain.User,
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
        ORDER BY random() LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': 10,  # FIXME
            'offset': 0,  # FIXME
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_ordered_nested_known(
            self,
            user: domain.User,
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
        ORDER BY number LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': 10,  # FIXME
            'offset': 0,  # FIXME
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_random_flat_known(
            self,
            user: domain.User,
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
        ORDER BY random() LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': 10,  # FIXME
            'offset': 0,  # FIXME
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]

    async def select_home_ordered_flat_known(
            self,
            user: domain.User,
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
        ORDER BY number LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': 10,  # FIXME
            'offset': 0,  # FIXME
        }

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item.from_map(row) for row in response]
