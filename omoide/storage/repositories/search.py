# -*- coding: utf-8 -*-
"""Search repository.
"""
import typing

from omoide.domain import auth, search, common
from omoide.domain.interfaces import database
from omoide.storage.repositories import base
from omoide.storage.repositories import search_sql


class SearchRepository(
    base.BaseRepository,
    database.AbsSearchRepository
):
    """Repository that performs all search queries."""
    _q_count_for_anon = search_sql.COUNT_ITEMS_FOR_ANON_USER
    _q_random_for_anon = search_sql.SEARCH_RANDOM_ITEMS_FOR_ANON_USER
    _q_specific_for_anon = search_sql.SEARCH_SPECIFIC_ITEMS_FOR_ANON_USER

    _q_count_for_user = None  # TODO(i.zyktin): need to add this
    _q_random_for_user = None  # TODO(i.zyktin): need to add this
    _q_specific_for_user = None  # TODO(i.zyktin): need to add this

    async def count_for_anon_user(self, user: auth.User) -> int:
        """Count available items for unauthorised user."""
        response = await self.db.fetch_one(self._q_count_for_anon)
        return response['total']

    async def search_random_items_for_anon_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find random items for unauthorised user."""
        total_items = await self.count_for_anon_user(user)

        response = await self.db.fetch_all(
            query=self._q_random_for_anon,
            values=self._values_without_tags(query)
        )

        items = [common.SimpleItem.from_row(row) for row in response]
        total_pages = int(total_items / (query.items_per_page or 1))

        return search.Result(
            is_random=True,
            page=query.page,
            total_items=total_items,
            total_pages=total_pages,
            items=items,
        )

    async def search_specific_items_for_anon_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find specific items for unauthorised user."""
        total_items = await self.count_for_anon_user(user)

        response = await self.db.fetch_all(
            query=self._q_specific_for_anon,
            values=self._values_with_tags(query)
        )

        items = [common.SimpleItem.from_row(row) for row in response]
        total_pages = int(total_items / (query.items_per_page or 1))

        return search.Result(
            is_random=False,
            page=query.page,
            total_items=total_items,
            total_pages=total_pages,
            items=items,
        )

    async def count_for_known_user(self, user: auth.User) -> int:
        """Count available items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    async def search_random_items_for_known_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find random items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    async def search_specific_items_for_known_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find specific items for authorised user."""
        # TODO(i.zyktin): need to implement this
        raise NotImplementedError

    @staticmethod
    def _values_without_tags(query: search.Query) -> dict[str, typing.Any]:
        """Format minimal values for the query."""
        offset = query.items_per_page * (query.page - 1)
        return {
            'limit': query.items_per_page,
            'offset': offset,
        }

    def _values_with_tags(self, query: search.Query) -> dict[str, typing.Any]:
        """Format regular values for the query."""
        values = self._values_without_tags(query)
        values['tags_include'] = query.tags_include
        values['tags_exclude'] = query.tags_exclude
        return values
