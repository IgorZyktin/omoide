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
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Perform request for home directory."""
        condition = {
            'anon': user.is_anon(),
            'ordered': aim.ordered,
            'nested': aim.nested,
        }

        async with self._repo.transaction():
            match condition:
                case {'anon': True, 'ordered': True, 'nested': False}:
                    items = await self._repo \
                        .select_home_ordered_flat_anon(aim)

                case {'anon': True, 'ordered': True, 'nested': True}:
                    items = await self._repo \
                        .select_home_ordered_nested_anon(aim)

                case {'anon': True, 'ordered': False, 'nested': False}:
                    items = await self._repo \
                        .select_home_random_flat_anon(aim)

                case {'anon': True, 'ordered': False, 'nested': True}:
                    items = await self._repo \
                        .select_home_random_nested_anon(aim)

                case {'anon': False, 'ordered': True, 'nested': False}:
                    items = await self._repo \
                        .select_home_ordered_flat_known(user, aim)

                case {'anon': False, 'ordered': True, 'nested': True}:
                    items = await self._repo \
                        .select_home_ordered_nested_known(user, aim)

                case {'anon': False, 'ordered': False, 'nested': False}:
                    items = await self._repo \
                        .select_home_random_flat_known(user, aim)

                case {'anon': False, 'ordered': False, 'nested': True}:
                    items = await self._repo \
                        .select_home_random_nested_known(user, aim)

                case _:
                    raise RuntimeError('Unknown aim set')

        return items
