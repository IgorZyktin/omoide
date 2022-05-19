# -*- coding: utf-8 -*-
"""Use case for home page.
"""
from omoide import domain
from omoide.domain import interfaces

__all__ = [
    'HomeUseCase',
]


class HomeUseCase:
    """Use case for home page."""

    def __init__(self, repo: interfaces.AbsHomeRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Perform request for home directory."""
        async with self._repo.transaction():
            if user.is_anon():
                items = await self._repo.find_home_items_for_anon(aim)
            else:
                items = await self._repo.find_home_items_for_known(user, aim)
        return items
