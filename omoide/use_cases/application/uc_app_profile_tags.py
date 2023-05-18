# -*- coding: utf-8 -*-
"""Use case for user profile tags.
"""
from omoide.domain import errors
from omoide.domain import models
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_search
from omoide.domain.special_types import Result
from omoide.domain.special_types import Success

__all__ = [
    'AppProfileTagsUseCase',
]


class AppProfileTagsUseCase:
    """Use case for user profile tags."""

    def __init__(
            self,
            search_repo: in_rp_search.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo

    async def execute(
            self,
            user: models.User,
    ) -> Result[errors.Error, list[tuple[str, int]]]:
        """Return tags with their counters."""
        async with self.search_repo.transaction():
            known_tags = await self.search_repo.count_all_tags(user)
        return Success(known_tags)
