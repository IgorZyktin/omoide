# -*- coding: utf-8 -*-
"""Use case for items.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces, exceptions

__all__ = [
    'GetItemUseCase',
]


class BaseItemUseCase:
    """Base use case."""

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self._repo = repo


class GetItemUseCase(BaseItemUseCase):
    """Use case for getting an item."""

    async def _assert_has_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> None:
        """Raise if user has no access to this item."""
        access = await self._repo.check_access(user, uuid)

        if access.does_not_exist:
            raise exceptions.NotFound(f'Item {uuid!r} does not exist')

        if access.is_not_given:
            raise exceptions.Forbidden(f'User {user.uuid!r} ({user.name!r}) '
                                       f'has no access to item {uuid!r}')

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.Item:
        """Business logic."""
        await self._assert_has_access(user, uuid)
        return await self._repo.get_item(uuid)
