# -*- coding: utf-8 -*-
"""Use case for home page.
"""
from omoide import domain
from omoide.domain import interfaces

from omoide.infra.special_types import Success

__all__ = [
    'AppHomeUseCase',
]


class AppHomeUseCase:
    """Use case for home page."""

    def __init__(self, browse_repo: interfaces.AbsBrowseRepository) -> None:
        """Initialize instance."""
        self.browse_repo = browse_repo

    async def execute(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> Success[list[domain.Item]]:
        """Perform request for home directory."""
        async with self.browse_repo.transaction():
            items = await self.browse_repo.simple_find_items_to_browse(
                user=user,
                uuid=None,
                aim=aim,
            )
        return Success(items)
