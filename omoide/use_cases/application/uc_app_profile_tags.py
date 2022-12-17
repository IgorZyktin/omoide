# -*- coding: utf-8 -*-
"""Use case for user profile tags.
"""
from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'AppProfileTagsUseCase',
]


class AppProfileTagsUseCase:
    """Use case for user profile tags."""

    def __init__(
            self,
            search_repo: interfaces.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo

    async def execute(
            self,
            user: domain.User,
    ) -> Result[errors.Error, list[tuple[str, int]]]:
        """Return tags with their counters."""
        if user.is_anon() or user.uuid is None:
            return Failure(errors.AuthenticationRequired())

        async with self.search_repo.transaction():
            known_tags = await self.search_repo.count_all_tags(user)

        return Success(known_tags)
