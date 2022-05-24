# -*- coding: utf-8 -*-
"""Use case for items.
"""
from uuid import UUID

from omoide import domain, utils
from omoide.domain import interfaces, exceptions

__all__ = [
    'AppDeleteItemUseCase',
]


class AppDeleteItemUseCase:
    """Use case for deleting an item."""

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            raw_uuid: str,
    ) -> tuple[int, domain.Item]:
        """Business logic."""
        if not utils.is_valid_uuid(raw_uuid):
            raise exceptions.IncorrectUUID(f'Bad uuid {raw_uuid!r}')

        uuid = UUID(raw_uuid)
        await self._repo.assert_has_access(user, uuid, only_for_owner=True)
        total = await self._repo.count_all_children(uuid)
        item = await self._repo.read_item(uuid)

        return total, item
