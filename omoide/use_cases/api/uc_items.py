# -*- coding: utf-8 -*-
"""Use case for items.
"""
from typing import Optional
from uuid import UUID

from omoide.presentation import api_models
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
            payload: api_models.CreateItemIn,
    ) -> UUID:
        """Business logic."""
        if user.cannot_create_items():
            raise exceptions.Forbidden('You are not allowed to create items')

        if payload.parent_uuid:
            await self._assert_has_access(user, payload.parent_uuid)
        else:
            payload.parent_uuid = user.root_item

        payload.uuid = await self._repo.generate_uuid()

        async with self._repo.transaction():
            uuid = await self._repo.create_item(user, payload)

        return uuid


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
            operations: list[api_models.PatchOperation],
    ) -> None:
        """Business logic."""
        await self._assert_has_access(user, uuid)
        item = await self._repo.read_item(uuid)

        if item is None:
            raise exceptions.NotFound(f'Item {uuid} does not exist')

        async with self._repo.transaction():
            for operation in operations:
                if operation.path == '/is_collection':
                    await self.alter_is_collection(item, operation)

    async def alter_is_collection(
            self,
            item: domain.Item,
            operation: api_models.PatchOperation,
    ) -> None:
        """Alter collection field."""
        item.is_collection = bool(operation.value)
        await self._repo.update_item(item)


class DeleteItemUseCase(BaseItemUseCase):
    """Use case for deleting an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> UUID:
        """Business logic."""
        await self._assert_has_access(user, uuid)

        item = await self._repo.read_item(uuid)
        parent_uuid = item.parent_uuid

        if parent_uuid is None:
            raise exceptions.Forbidden(f'You are not allowed '
                                       f'to delete root items')

        await self._repo.delete_item(uuid)

        return parent_uuid
