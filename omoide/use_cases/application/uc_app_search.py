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
        """Return amount of items that correspond to query (not items)."""
        async with self.search_repo.transaction():
            if user.is_anon():
                total = await self._search_for_anon(query, aim)
            else:
                total = await self._search_for_known(user, query, aim)
        return Success(total)

    async def _search_for_anon(
            self,
            query: domain.Query,
            aim: domain.Aim,
    ) -> int:
        """Count all possible search results for anon user."""
        total = 0
        if query:
            total = await self.search_repo \
                .count_matching_anon(query, aim)
        return total

    async def _search_for_known(
            self,
            user: domain.User,
            query: domain.Query,
            aim: domain.Aim,
    ) -> int:
        """Count all possible search results for known user."""
        total = 0
        if query:
            total = await self.search_repo \
                .count_matching_known(user, query, aim)
        return total


class AppPagedSearchUseCase(BaseSearchUseCase):
    """Use case for paged search."""

    async def execute(
            self,
            user: domain.User,
            query: domain.Query,
            details: domain.Details,
            aim: domain.Aim,
    ) -> Result[errors.Error, list[domain.Item]]:
        """Return items that correspond to query."""
        async with self.search_repo.transaction():
            if user.is_anon():
                items = await self._search_for_anon(query, details, aim)
            else:
                items = await self._search_for_known(user, query, details, aim)
        return Success(items)

    async def _search_for_anon(
            self,
            query: domain.Query,
            details: domain.Details,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Return corresponding items for anon user."""
        items = []
        if query:
            items = await self.search_repo \
                .search_paged_anon(query, details, aim)
        return items

    async def _search_for_known(
            self,
            user: domain.User,
            query: domain.Query,
            details: domain.Details,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Return corresponding items for known user."""
        items = []
        if query:
            items = await self.search_repo \
                .search_paged_known(user, query, details, aim)
        return items
