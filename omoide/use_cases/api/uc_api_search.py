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

        obligation = domain.Obligation(max_results=1000)
        async with self.search_repo.transaction():
            items = await self.search_repo \
                .get_matching_items(user, aim, obligation)

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
            guess: domain.GuessTag,
    ) -> Result[errors.Error, list[domain.GuessResult]]:
        """Return possible tags."""
        obligation = domain.Obligation(max_results=10)

        async with self.search_repo.transaction():
            if user.is_registered:
                variants = await self.search_repo \
                    .guess_tag_known(user, guess, obligation)
            else:
                variants = await self.search_repo \
                    .guess_tag_anon(user, guess, obligation)

        return Success(variants)
