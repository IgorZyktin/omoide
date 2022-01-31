# -*- coding: utf-8 -*-
"""Use case for search.
"""
from omoide.domain import search, auth, common
from omoide.domain.interfaces import database


class SearchUseCase:
    """Use case for search."""

    def __init__(self, repo: database.AbsSearchRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: auth.User,
            query: common.Query,
    ) -> search.Result:
        """Perform search request."""
        async with self._repo.transaction():
            if user.is_anon():
                result = await self._search_for_anon(user, query)
            else:
                result = await self._search_for_known(user, query)
        return result

    async def _search_for_anon(
            self,
            user: auth.User,
            query: common.Query,
    ) -> search.Result:
        """Perform search request for anon user."""
        if query:
            is_random = False
            total_items = await self._repo.total_specific_anon(user, query)
            items = await self._repo.search_specific_anon(user, query)

        else:
            is_random = True
            total_items = await self._repo.total_random_anon(user)
            items = await self._repo.search_random_anon(user, query)

        return search.Result(
            is_random=is_random,
            page=query.page,
            total_pages=query.calc_total_pages(total_items),
            total_items=total_items,
            items=items,
        )

    async def _search_for_known(
            self,
            user: auth.User,
            query: common.Query,
    ) -> search.Result:
        """Perform search request for known user."""
        total_items = await self._repo.total_specific_known(
            user=user,
            query=query,
        )

        if query:
            is_random = False
            items = await self._repo.search_specific_known(
                user=user,
                query=query,
            )

        else:
            is_random = True
            items = await self._repo.search_random_known(
                user=user,
                query=query,
            )

        return search.Result(
            is_random=is_random,
            page=query.page,
            total_pages=query.calc_total_pages(total_items),
            total_items=total_items,
            items=items,
        )
