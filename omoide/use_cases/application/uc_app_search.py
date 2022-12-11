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
            aim: domain.Aim,
    ) -> Result[errors.Error, int]:
        """Return amount of items that correspond to query (not items)."""
        async with self.search_repo.transaction():
            total = 0
            if aim.query:
                total = await self.search_repo.count_matching_items(user, aim)
        return Success(total)


class AppPagedSearchUseCase(BaseSearchUseCase):
    """Use case for paged search."""

    async def execute(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> Result[errors.Error, list[domain.Item]]:
        """Return items that correspond to query."""
        async with self.search_repo.transaction():
            items = []
            if aim.query:
                obligation = domain.Obligation(max_results=1000)
                items = await self.search_repo \
                    .get_matching_items(user, aim, obligation)
        return Success(items)
