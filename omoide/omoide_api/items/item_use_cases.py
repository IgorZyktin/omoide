"""Use cases for Item-related operations."""

from collections.abc import AsyncIterable
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from typing import Literal
from typing import NamedTuple
from uuid import UUID
from uuid import uuid4

import python_utilz as pu

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.domain import ensure
from omoide.object_storage import interfaces as object_interfaces

LOG = custom_logging.get_logger(__name__)


class ItemResult(NamedTuple):
    """Single-item lookup result with users referenced by its permissions."""

    item: models.Item
    users_map: dict[int, models.User | None]


class ItemsResult(NamedTuple):
    """Multi-item lookup result with users referenced by their permissions."""

    items: list[models.Item]
    users_map: dict[int, models.User | None]


class BaseItemUseCase:
    """Cache helpers and tag-propagation logic shared between item use cases.

    Subclasses MUST set the repo attributes they invoke through these
    helpers: ``self.users`` for ``_get_cached_user``, ``self.items`` for
    ``_get_cached_item`` and ``update_tags``, ``self.tags`` for
    ``_get_cached_computed_tags`` and ``update_tags``.
    """

    database: AbsDatabase
    items: db_interfaces.AbsItemsRepo
    users: db_interfaces.AbsUsersRepo
    tags: db_interfaces.AbsTagsRepo

    def __init__(self) -> None:
        """Initialize per-instance request caches."""
        self._users_cache: dict[int, models.User] = {}
        self._items_cache: dict[int, models.Item] = {}
        self._computed_tags_cache: dict[int, set[str]] = {}

    async def _get_cached_user(self, conn: Any, user_id: int) -> models.User:
        """Perform cached request."""
        user = self._users_cache.get(user_id)

        if user is not None:
            return user

        user = await self.users.get_by_id(conn, user_id)
        self._users_cache[user.id] = user
        return user

    async def _get_cached_item(self, conn: Any, item_id: int) -> models.Item:
        """Perform cached request."""
        item = self._items_cache.get(item_id)

        if item is not None:
            return item

        item = await self.items.get_by_id(conn, item_id)
        self._items_cache[item.id] = item
        return item

    async def _get_cached_computed_tags(self, conn: Any, item: models.Item) -> set[str]:
        """Perform cached request."""
        tags = self._computed_tags_cache.get(item.id)

        if tags is not None:
            return tags

        tags = await self.tags.get_computed_tags(conn, item)
        self._computed_tags_cache[item.id] = tags
        return tags

    async def update_tags(
        self,
        user: models.User,
        item: models.Item,
        conn: Any,
    ) -> dict[int, models.User | None]:
        """Increment all counters and calculate computed tags."""
        users_map: dict[int, models.User | None] = {user.id: user}

        if item.parent_id is None:
            parent_tags = set()
        else:
            parent = await self._get_cached_item(conn, item.parent_id)
            parent_tags = await self._get_cached_computed_tags(conn, parent)

            if not parent.is_collection:
                parent.is_collection = True
                await self.items.save(conn, parent)

        computed_tags = item.get_computed_tags(parent_tags)

        # for the item itself
        await self.tags.save_computed_tags(conn, item, computed_tags)

        # for the owner
        await self.tags.increment_known_tags_user(conn, user, computed_tags)

        # for anons
        if user.is_public:
            await self.tags.increment_known_tags_anon(conn, computed_tags)

        # for everyone, who can see this item
        for user_id in item.permissions:
            other_user = await self._get_cached_user(conn, user_id)
            users_map[user_id] = other_user
            await self.tags.increment_known_tags_user(conn, other_user, computed_tags)

        return users_map


class CreateOneItemUseCase(BaseItemUseCase):
    """Use case for creating one item."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
        tags: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta
        self.tags = tags

    async def execute(  # noqa: PLR0913 Too many arguments in function definition
        self,
        user: models.User,
        item_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str,
        number: int | None,
        is_collection: bool,
        tags: list[str],
        permissions: list[dict[str, UUID | str]],
        top_level: bool = False,
        connection: Any = None,
    ) -> models.Item:
        """Create single item."""
        ensure.registered(user, 'Anonymous users are not allowed to create items')

        if item_uuid is None:
            valid_uuid = uuid4()
        else:
            valid_uuid = item_uuid

        transaction: Any
        if connection is None:
            transaction = self.database.transaction
        else:

            @asynccontextmanager
            async def transaction() -> AsyncIterator[Any]:
                yield connection

        async with transaction() as conn:
            if top_level:
                ensure.admin(user, 'Only admin can create top-level items')
                parent = None
            elif parent_uuid is None:
                parent = await self.users.get_root_item(conn, user)
            else:
                parent = await self.items.get_by_uuid(conn, parent_uuid)
                ensure.owner(user, parent, 'Only owner can create child items')

            _permissions: set[int] = set()
            for human_readable_user in permissions:
                user_uuid = human_readable_user.get('uuid')
                if not isinstance(user_uuid, UUID):
                    continue
                local_user = await self.users.get_by_uuid(conn, user_uuid)
                _permissions.add(local_user.id)

            item = models.Item(
                id=-1,
                uuid=valid_uuid,
                parent_id=parent.id if parent is not None else None,
                parent_uuid=parent.uuid if parent is not None else None,
                owner_id=user.id,
                owner_uuid=user.uuid,
                name=name,
                status=models.Status.AVAILABLE if is_collection else models.Status.CREATED,
                number=number if number is not None else -1,
                is_collection=is_collection,
                content_ext=None,
                preview_ext=None,
                thumbnail_ext=None,
                tags=set(tags),
                permissions=_permissions,
                extras={},
            )

            item.id = await self.items.create(conn, item)

            metainfo = models.Metainfo(
                item_id=item.id,
                created_at=pu.now(),
                updated_at=pu.now(),
                deleted_at=None,
                user_time=None,
                content_type=None,
                content_size=None,
                preview_size=None,
                thumbnail_size=None,
                content_width=None,
                content_height=None,
                preview_width=None,
                preview_height=None,
                thumbnail_width=None,
                thumbnail_height=None,
            )

            await self.meta.create(conn, metainfo)

        LOG.info('User {user} created item: {item}', user=user, item=item)
        return item


class CreateManyItemsUseCase(BaseItemUseCase):
    """Use case for item creation."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
        tags: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta
        self.tags = tags

    async def execute(
        self,
        user: models.User,
        *items_in: dict[str, Any],
    ) -> ItemsResult:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to create items')

        items: list[models.Item] = []
        users_map: dict[int, models.User | None] = {user.id: user}

        sub_use_case = CreateOneItemUseCase(
            self.database, self.items, self.users, self.meta, self.tags
        )
        async with self.database.transaction() as conn:
            for raw_item in items_in:
                item = await sub_use_case.execute(user, **raw_item, connection=conn)
                items.append(item)
                new_users = await self.update_tags(user, item, conn)
                users_map.update(new_users)

        LOG.info(
            'User {user} created {total} items: {items}',
            user=user,
            total=len(items),
            items=items,
        )

        return ItemsResult(items=items, users_map=users_map)


class GetItemUseCase(BaseItemUseCase):
    """Use case for item getting."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.users = users

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> ItemResult:
        """Execute."""
        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            owner = await self.users.get_by_id(conn, item.owner_id)
            users_map: dict[int, models.User | None] = {user.id: user}

            if not any(
                (
                    owner.is_public,
                    item.owner_id == user.id,
                    user.id in item.permissions,
                )
            ):
                # NOTE - hiding the fact
                msg = 'Item {item_uuid} does not exist'
                raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

            for user_id in item.permissions:
                other_user = await self.users.get_by_id(conn, user_id)
                users_map[user_id] = other_user

        return ItemResult(item=item, users_map=users_map)


class GetManyItemsUseCase(BaseItemUseCase):
    """Use case for item getting."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.users = users

    async def execute(
        self,
        user: models.User,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> ItemsResult:
        """Execute."""
        async with self.database.transaction() as conn:
            if user.is_anon:
                items = await self.items.get_items_anon(conn, owner_uuid, parent_uuid, name, limit)
            else:
                items = await self.items.get_items_known(
                    conn, user, owner_uuid, parent_uuid, name, limit
                )

            users_map: dict[int, models.User | None] = {user.id: user}
            for item in items:
                for user_id in item.permissions:
                    if user_id in users_map:
                        continue
                    other_user = await self.users.get_by_id(conn, user_id)
                    users_map[user_id] = other_user

        return ItemsResult(items=items, users_map=users_map)


class UpdateItemUseCase(BaseItemUseCase):
    """Use case for item update."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        is_collection: bool,
    ) -> None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to update items')

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot update someone else's item")

            if item.is_collection == is_collection:
                return

            LOG.info('{} is updating {}', user, item)

            item.is_collection = is_collection
            await self.items.save(conn, item)


class RenameItemUseCase(BaseItemUseCase):
    """Use case for item rename."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        misc: db_interfaces.AbsMiscRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.misc = misc

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        name: str,
    ) -> int | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to rename items')

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot rename someone else's item")

            if item.name == name:
                return None

            LOG.info('{} is renaming {}', user, item)

            item.name = name
            await self.items.save(conn, item)

            operation_id = await self.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(item.uuid),
                },
            )

        return operation_id


class ChangeParentItemUseCase(BaseItemUseCase):
    """Use case for setting new parent item."""

    def __init__(  # noqa: PLR0913
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
        misc: db_interfaces.AbsMiscRepo,
        commands_repo: db_interfaces.AbsCommandsRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta
        self.misc = misc
        self.commands_repo = commands_repo

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        new_parent_uuid: UUID,
    ) -> list[int]:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to change item parents')

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot change someone else's item parents")

            if item.parent_uuid == new_parent_uuid:
                return []

            if item.parent_uuid is None:
                msg = 'You cannot change parent for the root item'
                raise exceptions.InvalidInputError(msg)

            old_parent = await self.items.get_by_uuid(conn, item.parent_uuid)
            new_parent = await self.items.get_by_uuid(conn, new_parent_uuid)
            is_child = await self.items.is_child(conn, item, new_parent)

            if is_child:
                msg = (
                    'Item {new_parent_uuid} is actually a child of {item_uuid}, '
                    'you will get circular link this way'
                )
                raise exceptions.InvalidInputError(
                    msg, new_parent_uuid=new_parent_uuid, item_uuid=item_uuid
                )

            if old_parent.owner_id != new_parent.owner_id:
                msg = 'Currently you cannot move an item from one owner to another'
                raise exceptions.InvalidInputError(msg)

            LOG.info(
                '{user} is setting {new_parent} as a parent '
                'for {item} (previous parent is {old_parent})',
                user=user,
                new_parent=new_parent,
                item=item,
                old_parent=old_parent,
            )

            item.parent_id = new_parent.id
            item.parent_uuid = new_parent.uuid
            await self.items.save(conn, item)

            if not new_parent.is_collection:
                new_parent.is_collection = True
                await self.items.save(conn, new_parent)

            operation_id_tags = await self.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(item.uuid),
                },
            )

            operation_id_old_parent = await self.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(old_parent.uuid),
                },
            )

            operation_id_new_parent = await self.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(new_parent.uuid),
                },
            )

            if new_parent.thumbnail_ext is None:
                await self.commands_repo.copy_image(
                    conn=conn,
                    requested_by=user,
                    source_item=item,
                    target_item=new_parent,
                )

        return [operation_id_tags, operation_id_old_parent, operation_id_new_parent]


class UpdateItemTagsUseCase(BaseItemUseCase):
    """Use case for item tags update."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        misc: db_interfaces.AbsMiscRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.misc = misc

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        tags: set[str],
    ) -> int | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to change item tags')

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot update someone else's item's tags")

            if item.tags == tags:
                return None

            LOG.info('{} is updating tags of {}', user, item)

            item.tags = tags
            await self.items.save(conn, item)

            operation_id = await self.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(item.uuid),
                },
            )

        return operation_id


class DeleteItemUseCase(BaseItemUseCase):
    """Use case for item deletion."""

    def __init__(  # noqa: PLR0913
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
        tags: db_interfaces.AbsTagsRepo,
        commands_repo: db_interfaces.AbsCommandsRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta
        self.tags = tags
        self.commands_repo = commands_repo

    async def execute(  # noqa: C901,PLR0912
        self,
        user: models.User,
        item_uuid: UUID,
        desired_switch: Literal['parent', 'sibling'],
    ) -> models.Item | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to delete items')
        switch_to = None

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot delete someone else's item")

            if item.parent_id is None:
                LOG.warning('{} tried to delete root {}', user, item)
                msg = 'Root items cannot be deleted'
                raise exceptions.NotAllowedError(msg)

            if desired_switch == 'sibling':
                siblings = await self.items.get_siblings(conn, item, collections=False)
                if item not in siblings:
                    desired_switch = 'parent'
                elif len(siblings) > 1:
                    index = siblings.index(item)
                    last = len(siblings) - 1

                    if index == last:
                        switch_to = siblings[last - 1]
                    else:
                        switch_to = siblings[index + 1]
                elif len(siblings) == 1:
                    switch_to = siblings[0]
                    if switch_to.id == item.id:
                        desired_switch = 'parent'
                else:
                    desired_switch = 'parent'

            if desired_switch == 'parent' or switch_to is None:
                switch_to = await self.items.get_by_id(conn, item.parent_id)

            members = await self.items.get_family(conn, item)
            for member in members:
                if member.id == item.id:
                    LOG.info('{} is soft deleting {}', user, item)
                else:
                    LOG.info('Deletion of {} caused deletion of {}', item, member)

                owner = await self._get_cached_user(conn, member.owner_id)
                computed_tags = await self._get_cached_computed_tags(conn, member)
                await self.tags.save_computed_tags(conn, member, set())
                await self.tags.decrement_known_tags_user(conn, owner, computed_tags)

                if owner.is_public:
                    await self.tags.decrement_known_tags_anon(conn, computed_tags)

                for user_id in member.permissions:
                    other_user = await self._get_cached_user(conn, user_id)
                    await self.tags.decrement_known_tags_user(conn, other_user, computed_tags)

                member_metainfo = await self.meta.get_by_item(conn, member)
                await self.commands_repo.soft_delete(conn, user, member)
                await self.meta.soft_delete(conn, member_metainfo)
                await self.items.soft_delete(conn, member)

        return switch_to


class UploadItemUseCase(BaseItemUseCase):
    """Use case for processing image binary content."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        meta: db_interfaces.AbsMetaRepo,
        misc: db_interfaces.AbsMiscRepo,
        storage: object_interfaces.AbsContentStorage,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.meta = meta
        self.misc = misc
        self.storage = storage

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        file: models.NewFile,
        chunks: AsyncIterable[bytes],
    ) -> int | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to upload items')

        # Pre-flight ownership check before the HTTP body is consumed.
        # Failing here avoids streaming the payload only to reject it.
        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot upload media to someone else's item")

        # Stream the upload into long-term storage with no DB transaction
        # held; the storage commits on its own session.
        reference = await self.storage.save(chunks)
        LOG.info('Saved upload for item {} as {}', item.uuid, reference)

        # Write all queue/metadata side effects in one short transaction.
        async with self.database.transaction() as conn:
            now = pu.now()

            operation_id = await self.misc.save_input_media(
                conn=conn,
                media=models.InputMedia(
                    id=-1,
                    user_uuid=user.uuid,
                    item_uuid=item.uuid,
                    created_at=now,
                    ext='jpg' if file.ext == 'jpeg' else file.ext,
                    content_type=file.content_type,
                    extras={'extract_exif': file.features.extract_exif, **reference},
                    error=None,
                    content=b'',
                ),
            )

            await self.meta.add_item_note(
                conn,
                item=item,
                key='original_filename',
                value=str(file.filename),
            )

            if item.parent_id is not None:
                parent = await self.items.get_by_id(conn, item.parent_id)
                parent.is_collection = True

                if parent.thumbnail_ext is None:
                    # NOTE - temporarily setting parent metainfo,
                    # so next item in batch will not copy again
                    parent.preview_ext = 'tmp'
                    parent.thumbnail_ext = 'tmp'

                    # Reuse the same long-term reference for the parent thumbnail.
                    # The converter only deletes the OID when no other queue
                    # entry still references it.
                    await self.misc.save_input_media(
                        conn=conn,
                        media=models.InputMedia(
                            id=-1,
                            user_uuid=user.uuid,
                            item_uuid=parent.uuid,
                            created_at=now,
                            ext='jpg' if file.ext == 'jpeg' else file.ext,
                            content_type=file.content_type,
                            extras={
                                'extract_exif': file.features.extract_exif,
                                'skip_content': True,
                                'skip_preview': True,
                                **reference,
                            },
                            error=None,
                            content=b'',
                        ),
                    )

                    await self.meta.add_item_note(
                        conn=conn,
                        item=parent,
                        key='copied_image_from',
                        value=str(item.uuid),
                    )

                await self.items.save(conn, parent)

        return operation_id


class ChangePermissionsUseCase(BaseItemUseCase):
    """Use case for item permissions change."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        misc: db_interfaces.AbsMiscRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__()
        self.database = database
        self.items = items
        self.users = users
        self.misc = misc

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        permissions: set[UUID],
        apply_to_parents: bool,
        apply_to_children: bool,
        apply_to_children_as: const.ApplyAs,
    ) -> int | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to change item permissions')

        operation_id = None

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot change someone else's item's permissions")

            LOG.info('{} is updating permissions of {}', user, item)

            user_ids: set[int] = set()
            for user_uuid in permissions:
                user = await self.users.get_by_uuid(conn, user_uuid)
                user_ids.add(user.id)

            if item.permissions == permissions:
                return None

            if apply_to_parents or apply_to_children:
                added, deleted = utils.get_delta(item.permissions, user_ids)

                operation_id = await self.misc.create_serial_operation(
                    conn=conn,
                    name='rebuild_permissions',
                    extras={
                        'requested_by': str(user.uuid),
                        'item_uuid': str(item.uuid),
                        'added': list(added),
                        'deleted': list(deleted),
                        'original': list(item.permissions),
                        'apply_to_parents': apply_to_parents,
                        'apply_to_children': apply_to_children,
                        'apply_to_children_as': apply_to_children_as.value,
                    },
                )

            item.permissions = user_ids
            await self.items.save(conn, item)

        return operation_id
