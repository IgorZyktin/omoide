# -*- coding: utf-8 -*-
"""Use case for search.
"""
from omoide.domain import search, auth, common
from omoide.domain.interfaces import repositories


class SearchUseCase:
    """Use case for search."""

    def __init__(self, repo: repositories.AbsSearchRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: auth.User,
            query: common.Query,
            details: common.Details,
    ) -> search.Result:
        """Perform search request."""
        async with self._repo.transaction():
            if user.is_anon():
                result = await self._search_for_anon(query, details)
            else:
                result = await self._search_for_known(user, query, details)
        return result

    async def _search_for_anon(
            self,
            query: common.Query,
            details: common.Details,
    ) -> search.Result:
        """Perform search request for anon user."""
        if query:
            is_random = False
            total_items = await self._repo.total_specific_anon(query)
            items = await self._repo.search_specific_anon(query, details)

        else:
            is_random = True
            total_items = await self._repo.total_random_anon()
            items = await self._repo.search_random_anon(query, details)

        return search.Result(
            is_random=is_random,
            page=details.page,
            total_pages=details.calc_total_pages(total_items),
            total_items=total_items,
            items=items,
        )

    async def _search_for_known(
            self,
            user: auth.User,
            query: common.Query,
            details: common.Details,
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
            page=details.page,
            total_pages=details.calc_total_pages(total_items),
            total_items=total_items,
            items=items,
        )
