# -*- coding: utf-8 -*-
"""By owner uuid search repository.
"""
from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base


class ByUserRepository(
    base.BaseRepository,
    interfaces.AbsByUserRepository,
):
    """Repository that performs search based on owner uuid."""

    async def count_items_of_public_user(
            self,
            owner_uuid: str,
    ) -> int:
        """Count all items of a public user."""
        query = """
        SELECT count(*) AS total_items
        FROM items
        WHERE owner_uuid = :owner_uuid
          AND parent_uuid IS NULL;
        """

        response = await self.db.fetch_one(query, {'owner_uuid': owner_uuid})
        return int(response['total_items'])

    async def get_items_of_public_user(
            self,
            owner_uuid: str,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Load all items of a public user."""
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
        WHERE owner_uuid = :owner_uuid
          AND parent_uuid IS NULL
          AND number > :anchor
        ORDER BY number LIMIT :limit;
        """

        values = {
            'owner_uuid': owner_uuid,
            'limit': details.items_per_page,
            'anchor': details.anchor,
        }

        response = await self.db.fetch_all(query, values)
        return [domain.Item.from_map(row) for row in response]

    async def count_items_of_private_user(
            self,
            user: domain.User,
            owner_uuid: str,
    ) -> int:
        """Count all items of a private user."""
        query = """
        SELECT count(*) AS total_items
        FROM items it
            RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE owner_uuid = :owner_uuid
          AND :user_uuid = ANY(cp.permissions)
          AND parent_uuid IS NULL;
        """

        values = {
            'user_uuid': user.uuid,
            'owner_uuid': owner_uuid,
        }

        response = await self.db.fetch_one(query, values)
        return int(response['total_items'])

    async def get_items_of_private_user(
            self,
            user: domain.User,
            owner_uuid: str,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Load all items of a private user."""
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
        FROM items it
            RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE owner_uuid = :owner_uuid
          AND :user_uuid = ANY(cp.permissions)
          AND parent_uuid IS NULL
          AND number > :anchor
        ORDER BY number LIMIT :limit;
        """

        values = {
            'user_uuid': user.uuid,
            'owner_uuid': owner_uuid,
            'limit': details.items_per_page,
            'anchor': details.anchor,
        }

        response = await self.db.fetch_all(query, values)
        return [domain.Item.from_map(row) for row in response]
