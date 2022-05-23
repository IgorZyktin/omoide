# -*- coding: utf-8 -*-
"""Use case for items.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces, exceptions

__all__ = [
    'CreateItemUseCase',
    'ReadItemUseCase',
    'UpdateItemUseCase',
    'DeleteItemUseCase',
]


class BaseItemUseCase:
    """Base use case."""

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def _assert_has_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Raise if user has no access to this item."""
        access = await self._repo.check_access(user, uuid)

        if access.does_not_exist:
            raise exceptions.NotFound(f'Item {uuid} does not exist')

        if access.is_not_given:
            raise exceptions.Forbidden(f'User {user.uuid} ({user.name}) '
                                       f'has no access to item {uuid}')

        if access.is_not_owner:
            raise exceptions.Forbidden(f'You must own item {uuid} '
                                       'to be able to modify it')

        return access


class CreateItemUseCase(BaseItemUseCase):
    """Use case for creating an item."""

    async def execute(
            self,
            user: domain.User,
            payload: domain.CreateItemIn,
    ) -> UUID:
        """Business logic."""
        if user.is_anon():
            raise exceptions.Forbidden('Anonymous users are not '
                                       'allowed to create items')

        if payload.parent_uuid:
            await self._repo.assert_has_access(user, payload.parent_uuid,
                                               only_for_owner=True)

        payload.uuid = await self._repo.generate_uuid()
        return await self._repo.create_item(user, payload)


class ReadItemUseCase(BaseItemUseCase):
    """Use case for getting an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.Item:
        """Business logic."""
        await self._repo.assert_has_access(user, uuid, only_for_owner=False)
        item = await self._repo.read_item(uuid)

        if item is None:
            raise exceptions.NotFound(f'Item {uuid} does not exist')

        return item


class UpdateItemUseCase(BaseItemUseCase):
    """Use case for updating an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> None:
        """Business logic."""
        # TODO(i.zyktin): implement item update


class DeleteItemUseCase(BaseItemUseCase):
    """Use case for deleting an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> None:
        """Business logic."""
        await self._repo.assert_has_access(user, uuid, only_for_owner=True)
        # TODO(i.zyktin): add records to the zombies table
        return await self._repo.delete_item(uuid)
