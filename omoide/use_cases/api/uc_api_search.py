# -*- coding: utf-8 -*-
"""Use cases for search.
"""
from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces

from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'ApiSearchUseCase',
]


class ApiSearchUseCase:
    """Use case for search (API)."""

    def __init__(
            self,
            search_repo: interfaces.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo

    async def execute(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> Result[errors.Error, list[domain.Item]]:
        """Perform search request."""
        if not aim.query:
            return Success([])

        assert not aim.paged

        async with self.search_repo.transaction():
            result = await self._search_dynamic(user, aim)

        return Success(result)

    async def _search_dynamic(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items in dynamic mode."""
        if user.is_anon():
            items = await self.search_repo.search_dynamic_anon(aim)
        else:
            items = await self.search_repo.search_dynamic_known(user, aim)
        return items
