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
            limit: int,
            offset: int,
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
        ORDER BY number LIMIT :limit OFFSET :offset
        """

        values = {
            'owner_uuid': owner_uuid,
            'limit': limit,
            'offset': offset,
        }

        response = await self.db.fetch_all(query, values)
        return [domain.Item.from_map(row) for row in response]

    async def count_items_of_private_user(
            self,
            user: domain.User,
            owner_uuid: str,
    ) -> int:
        """Count all items of a private user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    async def get_items_of_private_user(
            self,
            user: domain.User,
            owner_uuid: str,
            limit: int,
            offset: int,
    ) -> list[domain.Item]:
        """Load all items of a private user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError
