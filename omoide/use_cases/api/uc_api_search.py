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
    'ApiSuggestTagUseCase',
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
            items = await self.search_repo.get_matching_items(user, aim)

        return Success(items)


class ApiSuggestTagUseCase:
    """Help user by suggesting possible tags."""

    def __init__(
            self,
            search_repo: interfaces.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo

    async def execute(
            self,
            user: domain.User,
            text: str,
    ) -> Result[errors.Error, list[domain.Item]]:
        """Return possible tags."""
        # async with self.search_repo.transaction():
        #     pass

        variants = [
            text,
            f'{text}-alpha',
            f'{text}-beta',
            f'{text}-gamma',
        ]

        return Success(variants)
