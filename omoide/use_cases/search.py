# -*- coding: utf-8 -*-
"""Search use cases.
"""
from omoide.domain import search, auth
from omoide.domain.interfaces import database


class SearchUseCase:
    """Use case for search."""

    def __init__(self, repo: database.AbsSearchRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Perform search request."""
        if user.is_anon():
            if query:
                result = await self._repo.search_specific_items_for_anon_user(
                    user=user,
                    query=query,
                )
            else:
                result = await self._repo.search_random_items_for_anon_user(
                    user=user,
                    query=query,
                )
        else:
            if query:
                result = await self._repo.search_specific_items_for_known_user(
                    user=user,
                    query=query,
                )
            else:
                result = await self._repo.search_random_items_for_known_user(
                    user=user,
                    query=query,
                )
        return result
