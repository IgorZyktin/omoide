# -*- coding: utf-8 -*-
"""Use case for search.
"""
from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success


class AppSearchUseCase:
    """Use case for search."""

    def __init__(
            self,
            search_repo: interfaces.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo

    async def execute(
            self,
            user: domain.User,
            query: domain.Query,
    ) -> Result[errors.Error, int]:
        """Perform search request."""
        async with self.search_repo.transaction():
            if user.is_anon():
                result = await self._search_for_anon(query)
            else:
                result = await self._search_for_known(user, query)

        return Success(result)

    async def _search_for_anon(
            self,
            query: domain.Query,
    ) -> tuple[int, int]:
        """Perform search request for anon user."""
        total_items = await self.search_repo.total_items_anon()
        matching_items = await self.search_repo.total_matching_anon(query)
        return matching_items, total_items

    async def _search_for_known(
            self,
            user: domain.User,
            query: domain.Query,
    ) -> tuple[int, int]:
        """Perform search request for known user."""
        total_items = await self.search_repo.total_items_known(user)
        matching_items = await self.search_repo.total_matching_known(
            user=user,
            query=query,
        )
        return matching_items, total_items
