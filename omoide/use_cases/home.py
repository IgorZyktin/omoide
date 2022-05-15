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
            'ordered': aim.ordered,
            'nested': aim.nested,
        }

        async with self._repo.transaction():
            if user.is_anon():
                items = await self._repo.find_home_items_for_anon(aim)
            else:
                match condition:
                    case {'ordered': True, 'nested': False}:
                        items = await self._repo \
                            .select_home_ordered_flat_known(user, aim)

                    case {'ordered': True, 'nested': True}:
                        items = await self._repo \
                            .select_home_ordered_nested_known(user, aim)

                    case {'ordered': False, 'nested': False}:
                        items = await self._repo \
                            .select_home_random_flat_known(user, aim)

                    case {'ordered': False, 'nested': True}:
                        items = await self._repo \
                            .select_home_random_nested_known(user, aim)

                    case _:
                        raise RuntimeError('Unknown aim set')

        return items
