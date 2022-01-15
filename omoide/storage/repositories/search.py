# -*- coding: utf-8 -*-
"""Search repository.
"""
import typing

from omoide.domain import auth, search
from omoide.domain.interfaces import database
from omoide.storage.database import queries


class SearchRepository(database.AbsSearchRepository):
    """Repository that performs all search queries."""
    _q_random_for_anon = queries.SEARCH_RANDOM_ITEMS_FOR_ANON_USER
    _q_specific_for_anon = queries.SEARCH_SPECIFIC_ITEMS_FOR_ANON_USER

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    async def search_random_items_for_anon_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find random items for unauthorised user."""
        response = await self.db.fetch_all(
            query=self._q_random_for_anon,
            values=self._values_without_tags(query)
        )

        items, total_items, total_pages = self._cast_response(response, query)

        return search.Result(
            is_random=True,
            page=query.page,
            total_items=total_items,
            total_pages=total_pages,
            items=items,
        )

    async def search_random_items_for_known_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find random items for authorised user."""
        raise NotImplementedError

    async def search_specific_items_for_anon_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find specific items for unauthorised user."""
        response = await self.db.fetch_all(
            query=self._q_specific_for_anon,
            values=self._values_with_tags(query)
        )

        items, total_items, total_pages = self._cast_response(response, query)

        return search.Result(
            is_random=False,
            page=query.page,
            total_items=total_items,
            total_pages=total_pages,
            items=items,
        )

    async def search_specific_items_for_known_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find specific items for authorised user."""
        raise NotImplementedError

    @staticmethod
    def _values_without_tags(query: search.Query) -> dict[str, typing.Any]:
        """Format minimal values for the query."""
        offset = query.items_per_page * (query.page - 1)
        return {
            'limit': query.items_per_page,
            'offset': offset,
        }

    @staticmethod
    def _values_with_tags(query: search.Query) -> dict[str, typing.Any]:
        """Format regular values for the query."""
        offset = query.items_per_page * (query.page - 1)
        return {
            'limit': query.items_per_page,
            'offset': offset,
            'tags_in': query.tags_include + query.tags_include_implicit,
            # 'tags_out': query.tags_exclude + query.tags_exclude_implicit,
        }

    @staticmethod
    def _cast_item(raw_item) -> tuple[int, search.SimpleItem | None]:
        """Convert from db format to required model."""
        item = dict(raw_item)
        total_items = item.pop('full_count')
        print(item)

        if item['uuid'] is None:
            return 0, None

        def as_str(key: str) -> str | None:
            """Extract optional."""
            value = item[key]
            if value is None:
                return None
            return str(value)
        return (
            total_items,
            search.SimpleItem(
                owner_uuid=as_str('owner_uuid'),
                uuid=as_str('uuid'),
                is_collection=item['is_collection'],
                name=item['name'],
                ext=item['ext'],
            )
        )

    def _cast_response(
            self,
            response,
            query: search.Query,
    ) -> tuple[list[search.SimpleItem], int, int]:
        """Convert response to a semi complete search result."""
        total_items = 0
        items = []
        for row in response:
            total_items, item = self._cast_item(row)
            if item is not None:
                items.append(item)

        total_pages = int(total_items / (query.items_per_page or 1))

        return items, total_items, total_pages
