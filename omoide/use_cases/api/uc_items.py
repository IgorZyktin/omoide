# -*- coding: utf-8 -*-
"""Use case for items.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.presentation import api_models

__all__ = [
    'CreateItemUseCase',
    'ReadItemUseCase',
    'UpdateItemUseCase',
    'DeleteItemUseCase',
]


class BaseItemUseCase:
    """Base use case."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo


class CreateItemUseCase(BaseItemUseCase):
    """Use case for creating an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            payload: api_models.CreateItemIn,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        async with self.items_repo.transaction():
            parent_uuid = payload.parent_uuid or user.root_item
            error = await policy.is_restricted(user, parent_uuid,
                                               actions.Item.CREATE)

            if error:
                return Failure(error)

            payload.uuid = await self.items_repo.generate_uuid()
            uuid = await self.items_repo.create_item(user, payload)

        return Success(uuid)


class ReadItemUseCase(BaseItemUseCase):
    """Use case for getting an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, domain.Item]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.READ)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

        return Success(item)


class UpdateItemUseCase(BaseItemUseCase):
    """Use case for updating an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            operations: list[api_models.PatchOperation],
    ) -> Result[errors.Error, bool]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.UPDATE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            for operation in operations:
                if operation.path == '/is_collection':
                    await self.alter_is_collection(item, operation)

        return Success(True)

    async def alter_is_collection(
            self,
            item: domain.Item,
            operation: api_models.PatchOperation,
    ) -> None:
        """Alter collection field."""
        item.is_collection = bool(operation.value)
        await self.items_repo.update_item(item)


class DeleteItemUseCase(BaseItemUseCase):
    """Use case for deleting an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.DELETE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)
            parent_uuid = item.parent_uuid

            if parent_uuid is None:
                return Failure(errors.ItemNoDeleteForRoot(uuid=uuid))

            deleted = await self.items_repo.delete_item(uuid)

            if not deleted:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

        return Success(parent_uuid)
