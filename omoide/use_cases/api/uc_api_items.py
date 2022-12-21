# -*- coding: utf-8 -*-
"""Use case for items.
"""
import asyncio
import time
from uuid import UUID

from omoide import domain
from omoide import utils
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra import custom_logging
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.presentation import api_models

__all__ = [
    'ApiItemCreateUseCase',
    'ApiItemReadUseCase',
    'ApiItemUpdateUseCase',
    'ApiItemDeleteUseCase',
    'ApiCopyThumbnailUseCase',
    'ApiItemUpdateParentUseCase',
    'ApiItemUpdateTagsUseCase',
    'ApiItemUpdatePermissionsUseCase',
]

LOG = custom_logging.get_logger(__name__)


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


class BaseItemMediaUseCase:
    """Base use case."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
            media_repo: interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo
        self.media_repo = media_repo


class BaseItemModifyUseCase:
    """Base use case."""

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

    async def recalculate_known_tags(
            self,
            item: domain.Item,
            tags_added: list[str],
            tags_deleted: list[str],
    ) -> None:
        """Update counters for known tags."""
        is_public = await self.users_repo.user_is_public(item.owner_uuid)

        for user_uuid in item.permissions:
            if tags_added:
                await self.metainfo_repo \
                    .increase_known_tags_for_known_user(user_uuid, tags_added)

            if tags_deleted:
                await self.metainfo_repo \
                    .decrease_known_tags_for_known_user(user_uuid,
                                                        tags_deleted)
                await self.metainfo_repo \
                    .drop_unused_tags_for_known_user(user_uuid)

        if is_public:
            if tags_added:
                await self.metainfo_repo \
                    .increase_known_tags_for_anon_user(tags_added)

            if tags_deleted:
                await self.metainfo_repo \
                    .decrease_known_tags_for_anon_user(tags_deleted)

                await self.metainfo_repo.drop_unused_tags_for_anon_user()

    async def recalculate_known_tags_indirect(
            self,
            user_uuid: UUID,
            tags_added: list[str],
            tags_deleted: list[str],
    ) -> None:
        """Update counters for known tags via permission update."""
        if tags_added:
            await self.metainfo_repo \
                .increase_known_tags_for_known_user(user_uuid, tags_added)

        if tags_deleted:
            await self.metainfo_repo \
                .decrease_known_tags_for_known_user(user_uuid,
                                                    tags_deleted)

            await self.metainfo_repo \
                .drop_unused_tags_for_known_user(user_uuid)


class ApiItemCreateUseCase(BaseItemModifyUseCase):
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
            await self.recalculate_known_tags(item, item.tags, [])

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


class ApiItemUpdateUseCase(BaseItemUseCase):
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
                    item.name = str(operation.value)
                elif operation.path == '/is_collection':
                    item.is_collection = str(operation.value).lower() == 'true'
                elif operation.path == '/content_ext':
                    item.content_ext = (
                        str(operation.value) if operation.value else None)
                elif operation.path == '/preview_ext':
                    item.preview_ext = (
                        str(operation.value) if operation.value else None)
                elif operation.path == '/thumbnail_ext':
                    item.thumbnail_ext = (
                        str(operation.value) if operation.value else None)

            await self.items_repo.update_item(item)
            await self.metainfo_repo.mark_metainfo_updated(item.uuid,
                                                           utils.now())

        return Success(True)


class ApiItemUpdateTagsUseCase(BaseItemModifyUseCase):
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

            _tags_added, _tags_deleted = utils.get_delta(item.tags, new_tags)
            tags_added = list(_tags_added)
            tags_deleted = list(_tags_deleted)

            item.tags = new_tags

            await self.items_repo.update_item(item)
            await self.metainfo_repo.mark_metainfo_updated(item.uuid,
                                                           utils.now())
            await self.metainfo_repo.update_computed_tags(user, item)
            await self.recalculate_known_tags(item, tags_added, tags_deleted)

        # TODO - do it manually + consider updating known tags
        asyncio.create_task(
            self.items_repo.update_tags_in_children_of(user, item),
        )

        return Success(uuid)


class ApiItemUpdatePermissionsUseCase(BaseItemModifyUseCase):
    """Set new permissions for the item.

    Optionally for children and parents.
    """

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            new_permissions: api_models.NewPermissionsIn,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
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
            await self.metainfo_repo.mark_metainfo_updated(item.uuid,
                                                           utils.now())

        added, deleted = utils.get_delta(
            new_permissions.permissions_before,
            new_permissions.permissions_after,
        )

        if new_permissions.apply_to_parents:
            asyncio.create_task(
                self.update_permissions_in_parents(user, item, added, deleted)
            )

        # TODO - do it manually + consider updating known tags
        if new_permissions.apply_to_children:
            asyncio.create_task(
                self.items_repo.update_permissions_in_children(
                    user, item, new_permissions.override, added, deleted)
            )

        return Success(uuid)

    async def update_permissions_in_parents(
            self,
            user: domain.User,
            item: domain.Item,
            added: set[UUID],
            deleted: set[UUID],
    ) -> None:
        """Apply permissions change to all parents."""
        async with self.items_repo.transaction():
            parents = await self.items_repo.get_all_parent_uuids(user, item)

            if parents:
                start = time.perf_counter()

                LOG.info(
                    'Started updating permissions in '
                    'parents of: {} (added {}, deleted {})',
                    item.uuid,
                    sorted(str(x) for x in added),
                    sorted(str(x) for x in deleted),
                )

                for i, parent_uuid in enumerate(parents, start=1):
                    await self.items_repo \
                        .update_permissions(parent_uuid, False, added,
                                            deleted, item.permissions)

                    for user_uuid in added:
                        await self.recalculate_known_tags_indirect(
                            user_uuid, item.tags, [])

                    for user_uuid in deleted:
                        await self.recalculate_known_tags_indirect(
                            user_uuid, [], item.tags)

                    await self.metainfo_repo \
                        .mark_metainfo_updated(parent_uuid, utils.now())

                delta = time.perf_counter() - start
                LOG.info(
                    'Ended updating permissions in '
                    'parents of {}: {} operations, {:0.4f} sec',
                    item.uuid,
                    len(parents),
                    delta,
                )


class ApiItemDeleteUseCase(BaseItemModifyUseCase):
    """Use case for deleting an item."""

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

            await self.recalculate_known_tags(item, [], item.tags)

            await self.items_repo.mark_files_as_orphans(item, utils.now())
            deleted = await self.items_repo.delete_item(item)

            if not deleted:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

        return Success(parent_uuid)


class ApiCopyThumbnailUseCase(BaseItemMediaUseCase):
    """Use case for changing parent thumbnail."""

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

            await self.metainfo_repo.mark_metainfo_updated(
                target_uuid, utils.now())

            # TODO - consider also copying preview
            await self.media_repo.copy_media(
                owner_uuid=user.uuid,
                source_uuid=source_uuid,
                target_uuid=target_uuid,
                ext=source.thumbnail_ext,
                target_folder='thumbnail',
            )

        return Success(source_uuid)


class ApiItemUpdateParentUseCase(BaseItemMediaUseCase):
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

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            item.parent_uuid = new_parent_uuid
            await self.items_repo.update_item(item)
            parent = await self.items_repo.read_item(new_parent_uuid)

            if parent is None:
                return Failure(errors.ItemDoesNotExist(uuid=new_parent_uuid))

            if not parent.thumbnail_ext and item.thumbnail_ext:
                # TODO - consider also copying preview
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

        # TODO - do it manually + consider updating known tags
        asyncio.create_task(
            self.items_repo.update_tags_in_children_of(user, parent),
        )

        return Success(new_parent_uuid)
