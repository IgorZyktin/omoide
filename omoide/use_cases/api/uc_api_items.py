# -*- coding: utf-8 -*-
"""Use case for items.
"""
import asyncio
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
    'ApiItemCreateUseCase',
    'ApiItemReadUseCase',
    'UpdateItemUseCase',
    'ApiItemDeleteUseCase',
    'ApiItemAlterParentUseCase',
    'ApiItemAlterTagsUseCase',
]


class BaseItemUseCase:
    """Base use case."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo


class ApiItemCreateUseCase(BaseItemUseCase):
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


class ApiItemReadUseCase(BaseItemUseCase):
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
                if operation.path == '/name':
                    await self.alter_name(item, operation)
                elif operation.path == '/is_collection':
                    await self.alter_is_collection(item, operation)
                elif operation.path == '/content_ext':
                    await self.alter_content_ext(item, operation)
                elif operation.path == '/preview_ext':
                    await self.alter_preview_ext(item, operation)
                elif operation.path == '/thumbnail_ext':
                    await self.alter_thumbnail_ext(item, operation)

                # TODO - add validation

            await self.items_repo.update_item(item)

        return Success(True)

    @staticmethod
    async def alter_is_collection(
            item: domain.Item,
            operation: api_models.PatchOperation,
    ) -> None:
        """Alter collection field."""
        item.is_collection = bool(operation.value)

    @staticmethod
    async def alter_name(
            item: domain.Item,
            operation: api_models.PatchOperation,
    ) -> None:
        """Alter name field."""
        item.name = str(operation.value)

    @staticmethod
    async def alter_content_ext(
            item: domain.Item,
            operation: api_models.PatchOperation,
    ) -> None:
        """Alter content_ext field."""
        item.content_ext = str(operation.value) if operation.value else None

    @staticmethod
    async def alter_preview_ext(
            item: domain.Item,
            operation: api_models.PatchOperation,
    ) -> None:
        """Alter preview_ext field."""
        item.preview_ext = str(operation.value) if operation.value else None

    @staticmethod
    async def alter_thumbnail_ext(
            item: domain.Item,
            operation: api_models.PatchOperation,
    ) -> None:
        """Alter thumbnail_ext field."""
        item.thumbnail_ext = str(operation.value) if operation.value else None


class ApiItemDeleteUseCase(BaseItemUseCase):
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


class ApiItemAlterParentUseCase(BaseItemUseCase):
    """Use case for changing parent item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            new_parent_uuid: UUID,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        bad_parent_error = errors.ItemWrongParent(
            uuid=uuid,
            new_parent_uuid=new_parent_uuid,
        )

        if uuid == new_parent_uuid:
            return Failure(bad_parent_error)

        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.UPDATE)
            if error:
                return Failure(error)

            error = await policy.is_restricted(user, new_parent_uuid,
                                               actions.Item.UPDATE)
            if error:
                return Failure(error)

            is_child = await self.items_repo.check_child(uuid, new_parent_uuid)
            if is_child:
                return Failure(bad_parent_error)

            item = await self.items_repo.read_item(uuid)
            item.parent_uuid = new_parent_uuid
            await self.items_repo.update_item(item)
            parent = await self.items_repo.read_item(new_parent_uuid)

        asyncio.create_task(self.items_repo.update_tags_in_children(parent))

        return Success(new_parent_uuid)


class ApiItemAlterTagsUseCase(BaseItemUseCase):
    """Set new tags for the item + all children."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            new_tags: list[str],
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.UPDATE)
            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)
            item.tags = new_tags
            await self.items_repo.update_item(item)

        asyncio.create_task(self.items_repo.update_tags_in_children(item))

        return Success(uuid)
