# -*- coding: utf-8 -*-
"""Use case for browse.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces

__all__ = [
    'APIBrowseUseCase',
]


class APIBrowseUseCase:
    """Use case for browse (api)."""

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        access = await self._repo.check_access(user, uuid)

        if access.does_not_exist or access.is_not_given:
            return []

        async with self._repo.transaction():
            if aim.nested:
                items = await self._repo.simple_find_items_to_browse(
                    user=user,
                    uuid=uuid,
                    aim=aim,
                )

            else:
                items = await self._repo.complex_find_items_to_browse(
                    user=user,
                    uuid=uuid,
                    aim=aim,
                )

        return items
