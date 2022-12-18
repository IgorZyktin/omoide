# -*- coding: utf-8 -*-
"""Use case for items.
"""
import asyncio
from uuid import UUID

from omoide import domain
from omoide import utils
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
    'ApiCopyThumbnailUseCase',
    'ApiItemAlterParentUseCase',
    'ApiItemAlterTagsUseCase',
    'ApiItemAlterPermissionsUseCase',
]


class BaseItemUseCase:
    """Base use case."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo


class ApiItemCreateUseCase:
    """Use case for creating an item."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
            users_repo: interfaces.AbsUsersReadRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo
        self.users_repo = users_repo

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

            uuid = await self.items_repo.generate_item_uuid()

            item = domain.Item(
                uuid=uuid,
                parent_uuid=parent_uuid,
                owner_uuid=user.uuid,
                number=-1,
                name=payload.name,
                is_collection=payload.is_collection,
                content_ext=None,
                preview_ext=None,
                thumbnail_ext=None,
                tags=payload.tags,
                permissions=payload.permissions,
            )

            await self.items_repo.create_item(user, item)
            await self.metainfo_repo.create_empty_metainfo(user, item)
            await self.metainfo_repo.update_computed_tags(user, item)
            await self.metainfo_repo.update_computed_permissions(user, item)

            for user_uuid in item.permissions:
                await self.metainfo_repo \
                    .increase_known_tags_for_known_user(user_uuid, item.tags)

            if await self.users_repo.user_is_public(item.owner_uuid):
                await self.metainfo_repo \
                    .increase_known_tags_for_anon_user(item.tags)

        return Success(uuid)


class ApiItemReadUseCase:
    """Use case for getting an item."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, domain.Item]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.READ)
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
            error = await policy.is_restricted(user, uuid, actions.Item.UPDATE)

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
                # TODO - consider updating known tags

            await self.items_repo.update_item(item)
            metainfo = await self.metainfo_repo.read_metainfo(uuid)

            if metainfo is None:
                return Failure(errors.MetainfoDoesNotExist(uuid=uuid))

            metainfo.updated_at = utils.now()
            await self.metainfo_repo.update_metainfo(user, metainfo)

        return Success(True)

    @staticmethod
    async def alter_is_collection(
            item: domain.Item,
            operation: api_models.PatchOperation,
    ) -> None:
        """Alter collection field."""
        item.is_collection = str(operation.value).lower() == 'true'

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


class ApiItemDeleteUseCase:
    """Use case for deleting an item."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
            users_repo: interfaces.AbsUsersReadRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo
        self.users_repo = users_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.DELETE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            parent_uuid = item.parent_uuid

            if parent_uuid is None:
                return Failure(errors.ItemNoDeleteForRoot(uuid=uuid))

            deleted = await self.items_repo.delete_item(uuid)

            if not deleted:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            if item.permissions:
                for user_uuid in item.permissions:
                    await self.metainfo_repo \
                        .decrease_known_tags_for_known_user(user_uuid,
                                                            item.tags)

                await self.metainfo_repo \
                    .drop_unused_tags_for_known_user(user_uuid)

            if await self.users_repo.user_is_public(item.owner_uuid):
                await self.metainfo_repo \
                    .decrease_known_tags_for_anon_user(item.tags)

            await self.metainfo_repo.drop_unused_tags_for_anon_user(user_uuid)

        return Success(parent_uuid)


class ApiCopyThumbnailUseCase(BaseItemUseCase):
    """Use case for changing parent thumbnail."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
            media_repo: interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        super().__init__(items_repo, metainfo_repo)
        self.media_repo = media_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            source_uuid: UUID,
            target_uuid: UUID,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        if target_uuid == source_uuid:
            return Failure(errors.ItemItself(uuid=target_uuid))

        if user.uuid is None:
            return Failure(errors.ItemModificationByAnon())

        async with self.items_repo.transaction():

            error = await policy.is_restricted(user, source_uuid,
                                               actions.Item.UPDATE)
            if error:
                return Failure(error)

            error = await policy.is_restricted(user, target_uuid,
                                               actions.Item.UPDATE)
            if error:
                return Failure(error)

            source = await self.items_repo.read_item(source_uuid)

            if source is None:
                return Failure(errors.ItemDoesNotExist(uuid=source_uuid))

            if source.thumbnail_ext is None:
                return Failure(errors.ItemHasNoThumbnail(uuid=source_uuid))

            metainfo = await self.metainfo_repo.read_metainfo(target_uuid)

            if metainfo is None:
                return Failure(errors.MetainfoDoesNotExist(uuid=target_uuid))

            metainfo.updated_at = utils.now()
            await self.metainfo_repo.update_metainfo(user, metainfo)

            await self.media_repo.copy_media(
                owner_uuid=user.uuid,
                source_uuid=source_uuid,
                target_uuid=target_uuid,
                ext=source.thumbnail_ext,
                target_folder='thumbnail',
            )

        return Success(source_uuid)


class ApiItemAlterParentUseCase(BaseItemUseCase):
    """Use case for changing parent item."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
            media_repo: interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        super().__init__(items_repo, metainfo_repo)
        self.media_repo = media_repo

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

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            item.parent_uuid = new_parent_uuid
            await self.items_repo.update_item(item)
            parent = await self.items_repo.read_item(new_parent_uuid)

            if parent is None:
                return Failure(errors.ItemDoesNotExist(uuid=new_parent_uuid))

            if not parent.thumbnail_ext and item.thumbnail_ext:
                await self.media_repo.copy_media(
                    owner_uuid=parent.owner_uuid,
                    source_uuid=item.uuid,
                    target_uuid=parent.uuid,
                    ext=item.thumbnail_ext,
                    target_folder='thumbnail',
                )

            metainfo = await self.metainfo_repo.read_metainfo(uuid)

            if metainfo is None:
                return Failure(errors.MetainfoDoesNotExist(uuid=uuid))

            metainfo.updated_at = utils.now()
            await self.metainfo_repo.update_metainfo(user, metainfo)

        asyncio.create_task(
            self.items_repo.update_tags_in_children_of(user, parent),
        )
        # TODO - consider updating known tags

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
            error = await policy.is_restricted(user, uuid, actions.Item.UPDATE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            item.tags = new_tags
            await self.items_repo.update_item(item)

            metainfo = await self.metainfo_repo.read_metainfo(uuid)

            if metainfo is None:
                return Failure(errors.MetainfoDoesNotExist(uuid=uuid))

            metainfo.updated_at = utils.now()
            await self.metainfo_repo.update_metainfo(user, metainfo)

        asyncio.create_task(
            self.items_repo.update_tags_in_children_of(user, item),
        )
        # TODO - consider updating known tags

        return Success(uuid)


class ApiItemAlterPermissionsUseCase(BaseItemUseCase):
    """Set new permissions for the item.

    Optionally for children and parents.
    """

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            raw_new_permissions: api_models.NewPermissionsIn,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        for string in [*raw_new_permissions.permissions_before,
                       *raw_new_permissions.permissions_after]:
            if not utils.is_valid_uuid(string):
                return Failure(errors.InvalidUUID(uuid=string))

        new_permissions = domain.NewPermissions(
            apply_to_parents=raw_new_permissions.apply_to_parents,
            apply_to_children=raw_new_permissions.apply_to_children,
            override=raw_new_permissions.override,
            permissions_before={
                UUID(x) for x in raw_new_permissions.permissions_before
            },
            permissions_after={
                UUID(x) for x in raw_new_permissions.permissions_after
            },
        )

        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.UPDATE)
            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            item.permissions = list(new_permissions.permissions_after)
            await self.items_repo.update_item(item)

            metainfo = await self.metainfo_repo.read_metainfo(uuid)

            if metainfo is None:
                return Failure(errors.MetainfoDoesNotExist(uuid=uuid))

            metainfo.updated_at = utils.now()
            await self.metainfo_repo.update_metainfo(user, metainfo)

        if new_permissions.apply_to_parents:
            asyncio.create_task(
                self.items_repo.update_permissions_in_parents(
                    user, item, new_permissions)
            )

        if new_permissions.apply_to_children:
            asyncio.create_task(
                self.items_repo.update_permissions_in_children(
                    user, item, new_permissions)
            )
            # TODO - consider updating known tags

        return Success(uuid)
