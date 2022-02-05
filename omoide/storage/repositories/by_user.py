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
    _query_user_is_public = by_user_sql.USER_IS_PUBLIC
    _query_count_of_public_user = by_user_sql.COUNT_ITEMS_OF_PUBLIC_USER
    _query_get_items_of_public_user = by_user_sql.GET_ITEMS_OF_PUBLIC_USER
    _query_count_of_private_user = by_user_sql.COUNT_ITEMS_OF_PRIVATE_USER
    _query_get_items_of_private_user = by_user_sql.GET_ITEMS_OF_PRIVATE_USER

    async def user_is_public(
            self,
            owner_uuid: str,
    ) -> bool:
        """Return True if owner is a public user."""
        response = await self.db.fetch_one(
            query=self._query_user_is_public,
            values={
                'user_uuid': owner_uuid,
            }
        )
        return response is not None

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
        response = await self.db.fetch_all(
            query=self._query_get_items_of_public_user,
            values={
                'owner_uuid': owner_uuid,
                'limit': limit,
                'offset': offset,
            }
        )
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
