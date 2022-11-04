# -*- coding: utf-8 -*-
"""Use case for home page.
"""
from omoide import domain
from omoide.domain import interfaces

__all__ = [
    'AppHomeUseCase',
]


class AppHomeUseCase:
    """Use case for home page."""

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Perform request for home directory."""
        async with self._repo.transaction():
            items = await self._repo.simple_find_items_to_browse(
                user=user,
                uuid=None,
                aim=aim,
            )
        return items
