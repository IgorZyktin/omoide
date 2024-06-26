"""Use case for items.
"""
import asyncio
import time
import traceback
from contextlib import asynccontextmanager
from typing import AsyncIterator
from typing import Collection
from uuid import UUID

from omoide import domain
from omoide import use_cases
from omoide import utils
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.domain.interfaces import AbsPolicy
from omoide.domain.storage.interfaces.in_rp_media import AbsMediaRepository
from omoide.infra import custom_logging
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.presentation import api_models

__all__ = [
    'ApiItemCreateUseCase',
    'ApiItemCreateBulkUseCase',
    'ApiItemReadUseCase',
    'ApiItemReadByNameUseCase',
    'ApiItemUpdateUseCase',
    'ApiItemDeleteUseCase',
    'ApiItemsDownloadUseCase',
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
        status='started',
        started=utils.now(),
        extras=extras,
    )

    writeback = Writeback(operations=0)

    # noinspection PyBroadException
    try:
        yield writeback
    except Exception:
        status = 'fail'
        error = str(traceback.format_exc())
    else:
        status = 'done'
        error = ''

    delta = time.perf_counter() - start

    await metainfo_repo.finish_long_job(
        id=job_id,
        status=status,
        duration=delta,
        operations=writeback.operations,
        error=error,
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
    if user.uuid is not None:
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
    if user.uuid is not None:
        extras: dict[str, int | float | bool | str | None] = {}

        if override:
            extras.update({'override': True})

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
) -> AsyncIterator[Writeback]:
    """Helper that tracks updates in children."""
    if user.uuid is not None:
        call = _generic_call(
            metainfo_repo=metainfo_repo,
            job_name='tags-in-children',
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
            policy: AbsPolicy,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
            media_repo: AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        self.policy = policy
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo
        self.media_repo = media_repo


class BaseItemModifyUseCase:
    """Base use case."""

    def __init__(
            self,
            users_repo: interfaces.AbsUsersRepository,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
    ) -> None:
        """Initialize instance."""
        self.users_repo = users_repo
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo

    async def _create_one_item(
            self,
            user: domain.User,
            payload: api_models.CreateItemIn | api_models.CreateItemsIn,
    ) -> UUID:
        """Helper functions that handles creation of an item."""
        uuid = await self.items_repo.generate_item_uuid()

        item = domain.Item(
            uuid=uuid,
            parent_uuid=payload.parent_uuid or user.root_item,
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
        users = await self.users_repo.read_all_users(*payload.permissions)
        await self.metainfo_repo.apply_new_known_tags(users, item.tags, [])

        return uuid


class ApiItemCreateUseCase(BaseItemModifyUseCase):
    """Use case for creating an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            payload: api_models.CreateItemIn,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        LOG.warning(user)
        async with self.items_repo.transaction():
            parent_uuid = payload.parent_uuid or user.root_item
            error = await policy.is_restricted(user, parent_uuid,
                                               actions.Item.CREATE)
            if error:
                return Failure(error)

            uuid = await self._create_one_item(user, payload)

        return Success(uuid)


class ApiItemCreateBulkUseCase(BaseItemModifyUseCase):
    """Use case for creating many items at once."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            payload: api_models.CreateItemsIn,
    ) -> Result[errors.Error, list[UUID]]:
        """Business logic."""
        async with self.items_repo.transaction():
            parent_uuid = payload.parent_uuid or user.root_item
            error = await policy.is_restricted(user, parent_uuid,
                                               actions.Item.CREATE)
            if error:
                return Failure(error)

            uuids: list[UUID] = []
            for _ in range(payload.total):
                uuid = await self._create_one_item(user, payload)
                uuids.append(uuid)

        return Success(uuids)


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


class ApiItemReadByNameUseCase:
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
            name: str,
    ) -> Result[errors.Error, domain.Item]:
        """Business logic."""
        async with self.items_repo.transaction():
            item = await self.items_repo.read_item_by_name(user, name)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=name))

            error = await policy.is_restricted(
                user,
                item.uuid,
                actions.Item.READ,
            )

            if error:
                return Failure(error)

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
                    item.content_ext \
                        = (str(operation.value) if operation.value else None)
                elif operation.path == '/preview_ext':
                    item.preview_ext \
                        = (str(operation.value) if operation.value else None)
                elif operation.path == '/thumbnail_ext':
                    item.thumbnail_ext = \
                        (str(operation.value) if operation.value else None)
                elif operation.path == '/copied_image_from':
                    if operation.value \
                            and utils.is_valid_uuid(str(operation.value)):
                        uuid = UUID(str(operation.value))
                        metainfo = await self.metainfo_repo.read_metainfo(uuid)
                        metainfo.extras['copied_image_from'] \
                            = str(operation.value)
                        await self.metainfo_repo.update_metainfo(user,
                                                                 metainfo)
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

            await self.metainfo_repo.update_computed_tags(user, item)
            users = await self.users_repo.read_all_users(*item.permissions)
            users += [user]
            await self.metainfo_repo.apply_new_known_tags(
                users, added, deleted)

            await self.metainfo_repo.mark_metainfo_updated(item.uuid,
                                                           utils.now())

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
        operations = 0

        if added:
            await self.items_repo.add_tags(item.uuid, added)
            operations += 1

        if deleted:
            await self.items_repo.delete_tags(item.uuid, deleted)
            operations += 1

        users = await self.users_repo.read_all_users(*item.permissions)
        users += [user]
        await self.metainfo_repo.apply_new_known_tags(
            users, added, deleted)

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
        added: set[UUID] = set()
        deleted: set[UUID] = set()

        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.UPDATE)
            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            if new_permissions.override:
                item.permissions = list(new_permissions.permissions_after)
                await self.items_repo.update_item(item)

            else:
                added, deleted = utils.get_delta(
                    new_permissions.permissions_before,
                    new_permissions.permissions_after,
                )
                if added:
                    await self.items_repo.add_permissions(uuid, added)

                if deleted:
                    await self.items_repo.delete_permissions(uuid, deleted)

            await self.metainfo_repo.mark_metainfo_updated(item.uuid,
                                                           utils.now())

        if added or deleted:
            if new_permissions.apply_to_parents:
                asyncio.create_task(
                    self.update_permissions_in_parents(
                        user, item, added, deleted)
                )

        if new_permissions.apply_to_children:
            asyncio.create_task(
                self.update_permissions_in_children(
                    user, item, new_permissions.override,
                    added, deleted, new_permissions.permissions_after)
            )

        return Success(uuid)

    async def update_permissions_in_parents(
            self,
            user: domain.User,
            item: domain.Item,
            added: Collection[UUID],
            deleted: Collection[UUID],
    ) -> None:
        """Apply permissions change to all parents."""
        async with self.items_repo.transaction():
            parents = await self.items_repo.get_all_parents(user, item)

            if not parents:
                return

            async with track_update_permissions_in_parents(
                    self.metainfo_repo, user,
                    item, added, deleted) as writeback:
                writeback.operations = len(parents)
                for i, parent in enumerate(parents, start=1):
                    await self.items_repo \
                        .update_permissions(parent.uuid, False, added,
                                            deleted, item.permissions)
                    await self.metainfo_repo \
                        .mark_metainfo_updated(parent.uuid, utils.now())

                await self.metainfo_repo.update_computed_tags(user, item)

    async def update_permissions_in_children(
            self,
            user: domain.User,
            item: domain.Item,
            override: bool,
            added: Collection[UUID],
            deleted: Collection[UUID],
            all_permissions: Collection[UUID],
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
                        await self.items_repo.update_permissions(
                            uuid=child_uuid,
                            override=override,
                            added=added,
                            deleted=deleted,
                            all_permissions=all_permissions,
                        )
                        writeback.operations += 1

                        if added or deleted or override:
                            await self.metainfo_repo \
                                .mark_metainfo_updated(child_uuid, utils.now())

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

            if item.parent_uuid is None:
                return Failure(errors.ItemNoDeleteForRoot(uuid=uuid))

            users = await self.users_repo.read_all_users(*item.permissions)
            users += [user]

            await self.metainfo_repo.apply_new_known_tags(
                users=users,
                tags_added=[],
                tags_deleted=item.tags,
            )

            public_users = await self.users_repo.get_public_users_uuids()
            await self.metainfo_repo.drop_unused_tags(users, public_users)
            await self.items_repo.mark_files_as_orphans(item, utils.now())
            deleted = await self.items_repo.delete_item(item)

            if not deleted:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

        return Success(item.parent_uuid)


class ApiItemUpdateParentUseCase(BaseItemMediaUseCase):
    """Use case for changing parent item."""

    def __init__(
            self,
            policy: AbsPolicy,
            users_repo: interfaces.AbsUsersRepository,
            items_repo: interfaces.AbsItemsWriteRepository,
            metainfo_repo: interfaces.AbsMetainfoRepository,
            media_repo: AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        super().__init__(policy, items_repo, metainfo_repo, media_repo)
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
                nested_use_case = use_cases.ApiCopyImageUseCase(
                    policy,
                    self.items_repo,
                    self.metainfo_repo,
                    self.media_repo,
                )
                await nested_use_case.execute(
                    user=user,
                    source_uuid=item.uuid,
                    target_uuid=new_parent.uuid,
                )

            await self.metainfo_repo.mark_metainfo_updated(new_parent.uuid,
                                                           utils.now())
            if old_parent:
                added, deleted = utils.get_delta(old_parent.tags,
                                                 new_parent.tags)
            else:
                added = set(new_parent.tags)
                deleted = set()

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


class ApiItemsDownloadUseCase:
    """Use case for downloading whole group of items as zip archive."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsReadRepository,
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
    ) -> Result[
        errors.Error,
        tuple[domain.Item, list[dict[str, UUID | str | int]]],
    ]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.READ)

            if error:
                return Failure(error)

            parent = await self.items_repo.read_item(uuid)

            if parent is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            result = await self.metainfo_repo \
                .read_children_to_download(user, parent)

            if not result:
                return Success((parent, []))

        return Success((parent, result))
