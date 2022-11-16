# -*- coding: utf-8 -*-
"""Use case for search.
"""
from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'AppSearchUseCase',
]


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
            aim: domain.Aim,
    ) -> Result[errors.Error, int]:
        """Perform search request."""
        async with self.search_repo.transaction():
            if user.is_anon():
                result = await self._search_for_anon(query, aim)
            else:
                result = await self._search_for_known(user, query, aim)

        return Success(result)

    async def _search_for_anon(
            self,
            query: domain.Query,
            aim: domain.Aim,
    ) -> tuple[int, int]:
        """Perform search request for anon user."""
        if query:
            matching_items = await self.search_repo \
                .total_matching_anon(query, aim)
        else:
            matching_items = 0

        total_items = await self.search_repo.total_items_anon(aim)
        return matching_items, total_items

    async def _search_for_known(
            self,
            user: domain.User,
            query: domain.Query,
            aim: domain.Aim,
    ) -> tuple[int, int]:
        """Perform search request for known user."""
        if query:
            matching_items = await self.search_repo \
                .total_matching_known(user, query, aim)
        else:
            matching_items = 0

        total_items = await self.search_repo.total_items_known(user, aim)
        return matching_items, total_items
