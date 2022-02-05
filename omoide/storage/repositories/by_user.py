# -*- coding: utf-8 -*-
"""By owner uuid search repository.
"""
from omoide.domain import auth, common
from omoide.domain.interfaces import database
from omoide.storage.repositories import base
from omoide.storage.repositories import by_user_sql


class ByUserRepository(
    base.BaseRepository,
    database.AbsByUserRepository
):
    """Repository that performs search based on owner uuid."""
    _query_count_of_public_user = by_user_sql.COUNT_ITEMS_OF_PUBLIC_USER

    async def count_items_of_public_user(
            self,
            owner_uuid: str,
    ) -> int:
        """Count all items of a public user."""
        response = await self.db.fetch_one(
            query=self._query_count_of_public_user,
            values={
                'owner_uuid': owner_uuid,
            }
        )
        return int(response['total_items'])

    async def get_items_of_public_user(
            self,
            owner_uuid: str,
            limit: int,
            offset: int,
    ) -> list[common.Item]:
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
        return [common.Item.from_map(row) for row in response]

    async def count_items_of_private_user(
            self,
            user: auth.User,
            owner_uuid: str,
    ) -> int:
        """Count all items of a private user."""
        # FIXME
        raise
        response = await self.db.fetch_one(
            query=self._query_count_of_private_user,
            values={
                'user_uuid': owner_uuid,
            }
        )
        return int(response['total_items'])

    async def get_items_of_private_user(
            self,
            user: auth.User,
            owner_uuid: str,
            limit: int,
            offset: int,
    ) -> list[common.Item]:
        """Load all items of a private user."""
        # FIXME
        raise
        response = await self.db.fetch_one(
            query=self._query_get_items_of_public_user,
            values={
                'user_uuid': user.uuid,
                'owner_uuid': owner_uuid,
                'limit': limit,
                'offset': offset,
            }
        )
        return [common.Item.from_map(row) for row in response]
