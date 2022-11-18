# -*- coding: utf-8 -*-
"""Use cases for search.
"""
from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'AppDynamicSearchUseCase',
    'AppPagedSearchUseCase',
]


class BaseSearchUseCase:
    """Base case for all search use cases."""

    def __init__(
            self,
            search_repo: interfaces.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo


class AppDynamicSearchUseCase(BaseSearchUseCase):
    """Use case for dynamic search."""

    async def execute(
            self,
            user: domain.User,
            query: domain.Query,
            aim: domain.Aim,
    ) -> Result[errors.Error, int]:
        """Perform search request."""
        async with self.search_repo.transaction():
            if user.is_anon():
                matching_items = await self._search_for_anon(query, aim)
            else:
                matching_items = await self._search_for_known(user, query, aim)

        return Success(matching_items)

    async def _search_for_anon(
            self,
            query: domain.Query,
            aim: domain.Aim,
    ) -> int:
        """Calculate all possible search results for anon user."""
        if query:
            matching_items = await self.search_repo \
                .total_matching_anon(query, aim)
        else:
            matching_items = 0

        return matching_items

    async def _search_for_known(
            self,
            user: domain.User,
            query: domain.Query,
            aim: domain.Aim,
    ) -> int:
        """Calculate all possible search results for known user."""
        if query:
            matching_items = await self.search_repo \
                .total_matching_known(user, query, aim)
        else:
            matching_items = 0

        return matching_items


class AppPagedSearchUseCase(BaseSearchUseCase):
    """Use case for paged search."""
    # TODO
