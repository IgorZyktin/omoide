# -*- coding: utf-8 -*-
"""Use case for items.
"""
import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator
from typing import Callable
from typing import Collection
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


class Writeback:
    """Helper class that stores results for context manager."""

    def __init__(self, operations: int) -> None:
        """Initialize instance."""
        self.operations = operations


@asynccontextmanager
async def _generic_call(
        metainfo_repo: interfaces.AbsMetainfoRepository,
        job_name: str,
        job_description: str,
        user_uuid: UUID,
        item_uuid: UUID,
        added: Collection[str],
        deleted: Collection[str],
        extras: dict[str, int | float | bool | str | None],
) -> AsyncIterator[Writeback]:
    """Generic call used in context managers."""
    start = time.perf_counter()
    LOG.info(
        'Started {} of: {} (added {}, deleted {})',
        job_description,
        item_uuid,
        added,
        deleted,
    )

    job_id = await metainfo_repo.start_long_job(
        name=job_name,
        user_uuid=user_uuid,
        target_uuid=item_uuid,
        added=added,
        deleted=deleted,
        status='init',
        started=utils.now(),
        extras=extras,
    )

    writeback = Writeback(operations=0)

    # noinspection PyBroadException
    try:
        yield writeback
    except Exception:
        status = 'fail'
    else:
        status = 'done'

    delta = time.perf_counter() - start

    await metainfo_repo.finish_long_job(
        id=job_id,
        status=status,
        duration=delta,
        operations=writeback.operations,
    )

    LOG.info(
        'Ended {} of {}: {} operations, {:0.4f} sec, {}',
        job_description,
        item_uuid,
        writeback.operations,
        delta,
        status,
    )


@asynccontextmanager
async def track_update_permissions_in_parents(
        metainfo_repo: interfaces.AbsMetainfoRepository,
        user: domain.User,
        item: domain.Item,
        added: Collection[UUID],
        deleted: Collection[UUID],
) -> AsyncIterator[Writeback]:
    """Helper that tracks updates in parents."""
    assert user.is_registered

    call = _generic_call(
        metainfo_repo=metainfo_repo,
        job_name='permissions-in-parents',
        job_description='updating permissions in parents',
        user_uuid=user.uuid,
        item_uuid=item.uuid,
        added=sorted(str(x) for x in added),
        deleted=sorted(str(x) for x in deleted),
        extras={},
    )

    async with call as writeback:
        yield writeback


@asynccontextmanager
async def track_update_permissions_in_children(
        metainfo_repo: interfaces.AbsMetainfoRepository,
        user: domain.User,
        item: domain.Item,
        override: bool,
        added: Collection[UUID],
        deleted: Collection[UUID],
) -> AsyncIterator[Writeback]:
    """Helper that tracks updates in children."""
    assert user.is_registered

    if override:
        extras = {'override': True}
    else:
        extras = {}

    call = _generic_call(
        metainfo_repo=metainfo_repo,
        job_name='permissions-in-children',
        job_description='updating permissions in children',
        user_uuid=user.uuid,
        item_uuid=item.uuid,
        added=sorted(str(x) for x in added),
        deleted=sorted(str(x) for x in deleted),
        extras=extras,
    )

    async with call as writeback:
        yield writeback


@asynccontextmanager
async def track_update_tags_in_children(
        metainfo_repo: interfaces.AbsMetainfoRepository,
        user: domain.User,
        item: domain.Item,
        added: Collection[str],
        deleted: Collection[str],
) -> AsyncIterator[Callable[[int], None]]:
    """Helper that tracks updates in children."""
    assert user.is_registered

    call = _generic_call(
        metainfo_repo=metainfo_repo,
        job_name='permissions-in-children',
        job_description='updating tags in children',
        user_uuid=user.uuid,
        item_uuid=item.uuid,
        added=sorted(str(x) for x in added),
        deleted=sorted(str(x) for x in deleted),
        extras={},
    )

    async with call as writeback:
        yield writeback


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
            tags_added: Collection[str],
            tags_deleted: Collection[str],
    ) -> None:
        """Update counters for known tags."""
        for user_uuid in [*item.permissions, item.owner_uuid]:
            await self.recalculate_known_tags_indirect(
                user_uuid=user_uuid,
                tags_added=tags_added,
                tags_deleted=tags_deleted
            )

    async def recalculate_known_tags_indirect(
            self,
            user_uuid: UUID,
            tags_added: Collection[str],
            tags_deleted: Collection[str],
    ) -> None:
        """Update counters for known tags via permission update."""
        is_public = await self.users_repo.user_is_public(user_uuid)

        if not is_public:
            if tags_added:
                await self.metainfo_repo \
                    .increase_known_tags_for_known_user(user_uuid, tags_added)

            if tags_deleted:
                await self.metainfo_repo \
                    .decrease_known_tags_for_known_user(user_uuid,
                                                        tags_deleted)

                await self.metainfo_repo \
                    .drop_unused_tags_for_known_user(user_uuid)

        else:
            if tags_added:
                await self.metainfo_repo \
                    .increase_known_tags_for_anon_user(tags_added)

            if tags_deleted:
                await self.metainfo_repo \
                    .decrease_known_tags_for_anon_user(tags_deleted)

                await self.metainfo_repo.drop_unused_tags_for_anon_user()


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


class ApiItemUpdateUseCase:
    """Use case for updating an item."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo

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
            added = list(_tags_added)
            deleted = list(_tags_deleted)

            item.tags = new_tags

            await self.items_repo.update_item(item)
            await self.metainfo_repo.mark_metainfo_updated(item.uuid,
                                                           utils.now())
            await self.metainfo_repo.update_computed_tags(user, item)
            await self.recalculate_known_tags(item, added, deleted)

        async def update():
            async with self.items_repo.transaction():
                async with track_update_tags_in_children(
                        self.metainfo_repo, user, item, added, deleted
                ) as writeback:
                    operations = await self.update_tags_in_children_of(
                        user, item, added, deleted)
                    writeback.operations = operations

        if added or deleted:
            asyncio.create_task(update())

        return Success(uuid)

    async def update_tags_in_children_of(
            self,
            user: domain.User,
            item: domain.Item,
            added: Collection[str],
            deleted: Collection[str],
    ) -> int:
        """Apply tags change to all children."""
        await self.recalculate_known_tags(item, added, deleted)
        operations = 0

        if added:
            await self.items_repo.add_tags(item.uuid, added)
            operations += 1

        if deleted:
            await self.items_repo.delete_tags(item.uuid, deleted)
            operations += 1

        async def recursive(item_uuid: UUID) -> None:
            nonlocal operations
            children = await self.items_repo \
                .get_direct_children_uuids_of(user, item_uuid)

            for child_uuid in children:
                if added:
                    await self.items_repo.add_tags(child_uuid,
                                                   added)
                    operations += 1

                if deleted:
                    await self.items_repo.delete_tags(child_uuid,
                                                      deleted)
                    operations += 1

                await recursive(child_uuid)

        await recursive(item.uuid)

        return operations


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

        if added or deleted:
            if new_permissions.apply_to_parents:
                asyncio.create_task(
                    self.update_permissions_in_parents(
                        user, item, added, deleted)
                )

            if new_permissions.apply_to_children:
                asyncio.create_task(
                    self.update_permissions_in_children(
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

            if not parents:
                return

            async with track_update_permissions_in_parents(
                    self.metainfo_repo, user,
                    item, added, deleted, len(parents)) as writeback:
                writeback.operations = len(parents)
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
                        .update_computed_permissions(user, parent_uuid)
                    await self.metainfo_repo \
                        .mark_metainfo_updated(parent_uuid, utils.now())

    async def update_permissions_in_children(
            self,
            user: domain.User,
            item: domain.Item,
            override: bool,
            added: set[UUID],
            deleted: set[UUID],
    ) -> None:
        """Apply permissions change to all children."""
        async with self.items_repo.transaction():
            async with track_update_permissions_in_children(
                    self.metainfo_repo, user, item, override, added, deleted
            ) as writeback:

                async def recursive(item_uuid: UUID) -> None:
                    children = await self.items_repo \
                        .get_direct_children_uuids_of(user, item_uuid)

                    for child_uuid in children:
                        if added:
                            await self.items_repo.add_permissions(
                                child_uuid, added)
                            writeback.operations += 1

                        if deleted:
                            await self.items_repo.delete_permissions(
                                child_uuid, deleted)
                            writeback.operations += 1

                        if added or deleted:
                            await self.metainfo_repo \
                                .update_computed_permissions(user, child_uuid)
                            await self.metainfo_repo \
                                .mark_metainfo_updated(child_uuid, utils.now())
                            writeback.operations += 2

                        await recursive(child_uuid)

                await recursive(item.uuid)


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

            if source.preview_ext is None:
                return Failure(errors.ItemHasNoPreview(uuid=source_uuid))

            if source.thumbnail_ext is None:
                return Failure(errors.ItemHasNoThumbnail(uuid=source_uuid))

            await self.media_repo.copy_media(
                owner_uuid=user.uuid,
                source_uuid=source_uuid,
                target_uuid=target_uuid,
                ext=source.preview_ext,
                target_folder='preview',
            )

            await self.media_repo.copy_media(
                owner_uuid=user.uuid,
                source_uuid=source_uuid,
                target_uuid=target_uuid,
                ext=source.thumbnail_ext,
                target_folder='thumbnail',
            )

            await self.metainfo_repo.mark_metainfo_updated(
                target_uuid, utils.now())

        return Success(source_uuid)


class ApiItemUpdateParentUseCase(BaseItemMediaUseCase):
    """Use case for changing parent item."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
            users_repo: interfaces.AbsUsersReadRepository,
            media_repo: interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        super().__init__(items_repo, metainfo_repo, media_repo)
        self.users_repo = users_repo

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

            old_parent = None
            if item.parent_uuid is not None:
                old_parent = await self.items_repo.read_item(item.parent_uuid)
                if old_parent is None:
                    return Failure(errors.ItemDoesNotExist(
                        uuid=item.parent_uuid
                    ))

            item.parent_uuid = new_parent_uuid
            await self.items_repo.update_item(item)

            new_parent = await self.items_repo.read_item(new_parent_uuid)
            if new_parent is None:
                return Failure(errors.ItemDoesNotExist(uuid=new_parent_uuid))

            if not new_parent.thumbnail_ext and item.thumbnail_ext:
                nested_use_case = ApiCopyThumbnailUseCase(
                    self.items_repo,
                    self.metainfo_repo,
                    self.media_repo,
                )
                nested_result = await nested_use_case.execute(
                    policy=policy,
                    user=user,
                    source_uuid=item.uuid,
                    target_uuid=new_parent.uuid,
                )

                if isinstance(nested_result, Failure):
                    return nested_result

            await self.metainfo_repo.mark_metainfo_updated(new_parent.uuid,
                                                           utils.now())

            if old_parent:
                added, deleted = utils.get_delta(old_parent.tags,
                                                 new_parent.tags)
            else:
                added = new_parent.tags
                deleted = []

        asyncio.create_task(
            self.update_tags_in_children_of(user, new_parent, added, deleted)
        )

        return Success(new_parent_uuid)

    async def update_tags_in_children_of(
            self,
            user: domain.User,
            item: domain.Item,
            added: Collection[str],
            deleted: Collection[str],
    ) -> None:
        """Apply tags change to all children."""
        async with self.items_repo.transaction():
            async with track_update_tags_in_children(
                    self.metainfo_repo, user, item, added, deleted
            ) as writeback:
                nested_use_case = ApiItemUpdateTagsUseCase(
                    items_repo=self.items_repo,
                    metainfo_repo=self.metainfo_repo,
                    users_repo=self.users_repo,
                )
                total = await nested_use_case.update_tags_in_children_of(
                    user, item, added, deleted)

                writeback.operations = total
