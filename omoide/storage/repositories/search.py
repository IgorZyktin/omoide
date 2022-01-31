# -*- coding: utf-8 -*-
"""Search repository.
"""
from omoide.domain import auth, search, common
from omoide.domain.interfaces import database
from omoide.storage.repositories import base
from omoide.storage.repositories import search_sql


class SearchRepository(
    base.BaseRepository,
    database.AbsSearchRepository
):
    """Repository that performs all search queries."""
    _query_count_items_for_anon = search_sql.COUNT_ITEMS_FOR_ANON_USER
    _query_random_for_anon = search_sql.SEARCH_RANDOM_ITEMS_FOR_ANON_USER
    _query_specific_for_anon = search_sql.SEARCH_SPECIFIC_ITEMS_FOR_ANON_USER

    _q_count_for_user = None  # TODO(i.zyktin): need to add this
    _q_random_for_user = None  # TODO(i.zyktin): need to add this
    _q_specific_for_user = None  # TODO(i.zyktin): need to add this

    async def count_items_for_anon_user(
            self,
            user: auth.User,
            query: common.Query,
    ) -> int:
        """Count available items for unauthorised user."""
        response = await self.db.fetch_one(
            query=self._query_count_items_for_anon,
        )
        return response['total_items']

    async def search_random_items_for_anon_user(
            self,
            user: auth.User,
            query: common.Query,
    ) -> list[common.SimpleItem]:
        """Find random items for unauthorised user."""
        response = await self.db.fetch_all(
            query=self._query_random_for_anon,
            values={
                'limit': query.items_per_page,
                'offset': query.offset,
            }
        )
        return [common.SimpleItem.from_row(row) for row in response]

    async def search_specific_items_for_anon_user(
            self,
            user: auth.User,
            query: common.Query,
    ) -> list[common.SimpleItem]:
        """Find specific items for unauthorised user."""
        response = await self.db.fetch_all(
            query=self._query_specific_for_anon,
            values={
                'limit': query.items_per_page,
                'offset': query.offset,
                'tags_include': query.tags_include,
                'tags_exclude': query.tags_exclude,
            }
        )
        return [common.SimpleItem.from_row(row) for row in response]

    async def count_items_for_known_user(
            self,
            user: auth.User,
            query: common.Query,
    ) -> int:
        """Count available items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    async def search_random_items_for_known_user(
            self,
            user: auth.User,
            query: common.Query,
    ) -> search.Result:
        """Find random items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    async def search_specific_items_for_known_user(
            self,
            user: auth.User,
            query: common.Query,
    ) -> search.Result:
        """Find specific items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError
