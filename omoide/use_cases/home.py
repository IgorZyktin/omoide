# -*- coding: utf-8 -*-
"""Use case for home page.
"""
from omoide import domain
from omoide.domain import interfaces


class HomeUseCase:
    """Use case for home page."""

    def __init__(self, repo: interfaces.AbsHomeRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
    ) -> list[domain.Item]:
        """Perform request for home directory."""
        condition = {
            'anon': user.is_anon(),
            'ordered': True,  # FIXME
            'flat': False,  # FIXME
        }

        async with self._repo.transaction():
            match condition:
                case {'anon': True, 'ordered': True, 'flat': True}:
                    items = await self._repo.select_home_ordered_flat_anon()
                case {'anon': True, 'ordered': True, 'flat': False}:
                    items = await self._repo.select_home_ordered_nested_anon()
                case {'anon': True, 'ordered': False, 'flat': True}:
                    items = await self._repo.select_home_random_flat_anon()
                case {'anon': True, 'ordered': False, 'flat': False}:
                    items = await self._repo.select_home_random_nested_anon()
                case {'anon': False, 'ordered': True, 'flat': True}:
                    items = await self._repo.select_home_ordered_flat_known(
                        user)
                case {'anon': False, 'ordered': True, 'flat': False}:
                    items = await self._repo.select_home_ordered_nested_known(
                        user)
                case {'anon': False, 'ordered': False, 'flat': True}:
                    items = await self._repo.select_home_random_flat_known(
                        user)
                case {'anon': False, 'ordered': False, 'flat': False}:
                    items = await self._repo.select_home_random_nested_known(
                        user)
                case _:
                    items = await self._repo.select_home_random_flat_anon()

        return items
