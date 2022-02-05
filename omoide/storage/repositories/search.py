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
    _query_total_random_anon = search_sql.TOTAL_RANDOM_ANON
    _query_total_specific_anon = search_sql.TOTAL_SPECIFIC_ANON
    _query_search_random_anon = search_sql.SEARCH_RANDOM_ANON
    _query_search_specific_anon = search_sql.SEARCH_SPECIFIC_ANON

    _q_count_for_user = None  # TODO(i.zyktin): need to add this
    _q_random_for_user = None  # TODO(i.zyktin): need to add this
    _q_specific_for_user = None  # TODO(i.zyktin): need to add this

    async def total_random_anon(
            self,
            user: auth.User,
    ) -> int:
        """Count all available items for unauthorised user."""
        response = await self.db.fetch_one(
            query=self._query_total_random_anon,
        )
        return response['total_items']

    async def total_specific_anon(
            self,
            user: auth.User,
            query: common.Query,
    ) -> int:
        """Count available items for unauthorised user."""
        response = await self.db.fetch_one(
            query=self._query_total_specific_anon,
            values={
                'tags_include': query.tags_include,
                'tags_exclude': query.tags_exclude,
            },
        )
        return response['total_items']

    async def search_random_anon(
            self,
            user: auth.User,
            query: common.Query,
    ) -> list[common.Item]:
        """Find random items for unauthorised user."""
        response = await self.db.fetch_all(
            query=self._query_search_random_anon,
            values={
                'limit': query.items_per_page,
                'offset': query.offset,
            }
        )
        return [common.Item.from_map(row) for row in response]

    async def search_specific_anon(
            self,
            user: auth.User,
            query: common.Query,
    ) -> list[common.Item]:
        """Find specific items for unauthorised user."""
        response = await self.db.fetch_all(
            query=self._query_search_specific_anon,
            values={
                'limit': query.items_per_page,
                'offset': query.offset,
                'tags_include': query.tags_include,
                'tags_exclude': query.tags_exclude,
            }
        )
        return [common.Item.from_map(row) for row in response]

    async def total_random_known(
            self,
            user: auth.User,
    ) -> int:
        """Count all available items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    async def total_specific_known(
            self,
            user: auth.User,
            query: common.Query,
    ) -> int:
        """Count available items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    async def search_random_known(
            self,
            user: auth.User,
            query: common.Query,
    ) -> search.Result:
        """Find random items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    async def search_specific_known(
            self,
            user: auth.User,
            query: common.Query,
    ) -> search.Result:
        """Find specific items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError
