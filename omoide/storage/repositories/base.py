# -*- coding: utf-8 -*-
"""Base functionality for all concrete repositories.
"""
import typing

from omoide.domain import auth, common
from omoide.domain.interfaces import database
from omoide.storage.repositories import base_sql


class BaseRepository(database.AbsRepository):
    """Base functionality for all concrete repositories."""
    _query_check_access = base_sql.CHECK_ACCESS
    _query_get_ancestors = base_sql.GET_ANCESTORS
    _query_get_owner = base_sql.GET_OWNER

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    def transaction(self) -> typing.Any:
        """Start transaction."""
        return self.db.transaction()

    async def check_access(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> common.AccessStatus:
        """Check access to the item."""
        response = await self.db.fetch_one(
            query=self._query_check_access,
            values={
                'user_uuid': user.uuid,
                'item_uuid': item_uuid,
            }
        )

        if response is None:
            return common.AccessStatus.not_found()

        return common.AccessStatus(
            exists=True,
            is_public=bool(response['is_public']),
            is_given=bool(response['is_given']),
        )

    async def get_location(self, item_uuid: str) -> common.Location:
        """Return Location of the item."""
        ancestors_response = await self.db.fetch_all(
            query=self._query_get_ancestors,
            values={
                'item_uuid': item_uuid,
            }
        )

        if ancestors_response is None or not ancestors_response:
            return common.Location.empty()

        items = [common.SimpleItem.from_row(x) for x in ancestors_response]

        parent_response = await self.db.fetch_one(
            query=self._query_get_owner,
            values={
                'user_uuid': items[-1].owner_uuid,
            }
        )

        if parent_response is None:
            return common.Location.empty()

        items.reverse()

        return common.Location(
            owner=common.SimpleUser.from_row(parent_response),
            items=items,
        )
