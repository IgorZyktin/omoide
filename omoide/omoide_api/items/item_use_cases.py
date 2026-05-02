"""Use cases for Item-related operations."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from typing import Literal
from uuid import UUID
from uuid import uuid4

import python_utilz as pu

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.domain import ensure
from omoide.infra import mediators

LOG = custom_logging.get_logger(__name__)


class CreateOneItemUseCase:
    """Use case for creating one item."""

    def __init__(self, mediator: mediators.UsersMediator | mediators.ItemsMediator) -> None:
        """Initialize instance."""
        self.mediator = mediator

    async def execute(  # noqa: PLR0913 Too many arguments in function definition
        self,
        user: models.User,
        uuid: UUID | None,
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
        if uuid is None:
            valid_uuid = uuid4()
        else:
            valid_uuid = uuid

        msg = 'You are not allowed to create items for other users'

        transaction: Any
        if connection is None:
            transaction = self.mediator.database.transaction()
        else:

            @asynccontextmanager
            async def transaction() -> AsyncIterator[Any]:
                yield conn

        async with transaction as conn:
            if top_level:
                parent = None
            elif parent_uuid is None:
                parent = await self.mediator.users.get_root_item(conn, user)
            else:
                parent = await self.mediator.items.get_by_uuid(conn, parent_uuid)
                if parent.owner_uuid != user.uuid:
                    raise exceptions.NotAllowedError(msg)

            _permissions: set[int] = set()
            for human_readable_user in permissions:
                user_uuid = human_readable_user.get('uuid')
                if not isinstance(user_uuid, UUID):
                    continue
                local_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
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
                number=number or -1,
                is_collection=is_collection,
                content_ext=None,
                preview_ext=None,
                thumbnail_ext=None,
                tags=set(tags),
                permissions=_permissions,
                extras={},
            )

            item.id = await self.mediator.items.create(conn, item)

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

            await self.mediator.meta.create(conn, metainfo)

        return item


class BaseItemUseCase:
    """Base use case for user-related operations."""

    def __init__(self, mediator: mediators.ItemsMediator) -> None:
        """Initialize instance."""
        self.mediator = mediator
        self._users_cache: dict[int, models.User] = {}
        self._items_cache: dict[int, models.Item] = {}
        self._computed_tags_cache: dict[int, set[str]] = {}

    async def _get_cached_user(self, conn: Any, user_id: int) -> models.User:
        """Perform cached request."""
        user = self._users_cache.get(user_id)

        if user is not None:
            return user

        user = await self.mediator.users.get_by_id(conn, user_id)
        self._users_cache[user.id] = user
        return user

    async def _get_cached_item(self, conn: Any, item_id: int) -> models.Item:
        """Perform cached request."""
        item = self._items_cache.get(item_id)

        if item is not None:
            return item

        item = await self.mediator.items.get_by_id(conn, item_id)
        self._items_cache[item.id] = item
        return item

    async def _get_cached_computed_tags(self, conn: Any, item: models.Item) -> set[str]:
        """Perform cached request."""
        tags = self._computed_tags_cache.get(item.id)

        if tags is not None:
            return tags

        tags = await self.mediator.tags.get_computed_tags(conn, item)
        self._computed_tags_cache[item.id] = tags
        return tags


class CreateManyItemsUseCase(BaseItemUseCase):
    """Use case for item creation."""

    async def execute(
        self,
        user: models.User,
        *items_in: dict[str, Any],
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to create items')

        items: list[models.Item] = []
        users_map: dict[int, models.User | None] = {user.id: user}

        sub_use_case = CreateOneItemUseCase(self.mediator)
        async with self.mediator.database.transaction() as conn:
            for raw_item in items_in:
                item = await sub_use_case.execute(user, **raw_item, connection=conn)
                items.append(item)

                if item.parent_id is None:
                    parent_tags = set()
                    parent_name = ''
                else:
                    parent = await self._get_cached_item(conn, item.parent_id)
                    parent_tags = await self._get_cached_computed_tags(conn, parent)
                    parent_name = parent.name

                    if not parent.is_collection:
                        parent.is_collection = True
                        await self.mediator.items.save(conn, parent)

                computed_tags = item.get_computed_tags(parent_name, parent_tags)

                # for the item itself
                await self.mediator.tags.save_computed_tags(conn, item, computed_tags)

                # for the owner
                await self.mediator.tags.increment_known_tags_user(conn, user, computed_tags)

                # for anons
                if user.is_public:
                    await self.mediator.tags.increment_known_tags_anon(conn, computed_tags)

                # for everyone, who can see this item
                for user_id in item.permissions:
                    other_user = await self._get_cached_user(conn, user_id)
                    users_map[user_id] = other_user
                    await self.mediator.tags.increment_known_tags_user(
                        conn, other_user, computed_tags
                    )

        if len(items) == 1:
            LOG.info('User {user} created item: {item}', user=user, item=items[0])
        else:
            LOG.info(
                'User {user} created {total} items: {items}',
                user=user,
                total=len(items),
                items=items,
            )

        return items, users_map


class GetItemUseCase(BaseItemUseCase):
    """Use case for item getting."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> tuple[models.Item, dict[int, models.User | None]]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)
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
                other_user = await self.mediator.users.get_by_id(conn, user_id)
                users_map[user_id] = other_user

        return item, users_map


class GetManyItemsUseCase(BaseItemUseCase):
    """Use case for item getting."""

    async def execute(
        self,
        user: models.User,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            if user.is_anon:
                items = await self.mediator.items.get_items_anon(
                    conn, owner_uuid, parent_uuid, name, limit
                )
            else:
                items = await self.mediator.items.get_items_known(
                    conn, user, owner_uuid, parent_uuid, name, limit
                )

            users_map: dict[int, models.User | None] = {user.id: user}
            for item in items:
                for user_id in item.permissions:
                    if user_id in users_map:
                        continue
                    other_user = await self.mediator.users.get_by_id(conn, user_id)
                    users_map[user_id] = other_user

        return items, users_map


class UpdateItemUseCase(BaseItemUseCase):
    """Use case for item update."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        is_collection: bool,
    ) -> None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to update items')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot update someone else's item")

            if item.is_collection == is_collection:
                return

            LOG.info('{} is updating {}', user, item)

            item.is_collection = is_collection
            await self.mediator.items.save(conn, item)


class RenameItemUseCase(BaseItemUseCase):
    """Use case for item rename."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        name: str,
    ) -> int | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to rename items')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot rename someone else's item")

            if item.name == name:
                return None

            LOG.info('{} is renaming {}', user, item)

            item.name = name
            await self.mediator.items.save(conn, item)

            operation_id = await self.mediator.misc.create_serial_operation(
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

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        new_parent_uuid: UUID,
    ) -> list[int]:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to change item parents')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot change someone else's item parents")

            if item.parent_uuid == new_parent_uuid:
                return []

            if item.parent_uuid is None:
                msg = 'You cannot change parent for the root item'
                raise exceptions.InvalidInputError(msg)

            old_parent = await self.mediator.items.get_by_uuid(conn, item.parent_uuid)
            new_parent = await self.mediator.items.get_by_uuid(conn, new_parent_uuid)
            is_child = await self.mediator.items.is_child(conn, item, new_parent)

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
            await self.mediator.items.save(conn, item)

            if not new_parent.is_collection:
                new_parent.is_collection = True
                await self.mediator.items.save(conn, new_parent)

            operation_id_tags = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(item.uuid),
                },
            )

            operation_id_old_parent = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(old_parent.uuid),
                },
            )

            operation_id_new_parent = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(new_parent.uuid),
                },
            )
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)

        if new_parent.thumbnail_ext is None:
            media_types = await self.mediator.object_storage.copy_all_objects(
                requested_by=user,
                owner=owner,
                source_item=item,
                target_item=new_parent,
            )

            if media_types:
                async with self.mediator.database.transaction() as conn:
                    await self.mediator.meta.add_item_note(
                        conn=conn,
                        item=new_parent,
                        key='copied_image_from',
                        value=str(item.uuid),
                    )

        return [operation_id_tags, operation_id_old_parent, operation_id_new_parent]


class UpdateItemTagsUseCase(BaseItemUseCase):
    """Use case for item tags update."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        tags: set[str],
    ) -> int | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to change item tags')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot update someone else's item's tags")

            if item.tags == tags:
                return None

            LOG.info('{} is updating tags of {}', user, item)

            item.tags = tags
            await self.mediator.items.save(conn, item)

            operation_id = await self.mediator.misc.create_serial_operation(
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

    async def execute(  # noqa: C901,PLR0912
        self,
        user: models.User,
        item_uuid: UUID,
        desired_switch: Literal['parent', 'sibling'],
    ) -> models.Item | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to delete items')
        switch_to = None

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot delete someone else's item")

            if item.parent_uuid is None:
                LOG.warning('{} tried to delete root {}', user, item)
                msg = 'Root items cannot be deleted'
                raise exceptions.NotAllowedError(msg)

            if desired_switch == 'sibling':
                siblings = await self.mediator.items.get_siblings(conn, item, collections=False)
                if item not in siblings:
                    desired_switch = 'parent'
                elif len(siblings) > 1:
                    index = siblings.index(item)
                    last = len(siblings) - 1

                    if index == len(siblings) - 1:
                        switch_to = siblings[last - 1]
                    else:
                        switch_to = siblings[index + 1]
                elif len(siblings) == 1:
                    switch_to = siblings[0]
                else:
                    desired_switch = 'parent'

            if (desired_switch == 'parent' or switch_to is None) and item.parent_id is not None:
                switch_to = await self.mediator.items.get_by_id(conn, item.parent_id)

            members = await self.mediator.items.get_family(conn, item)
            for member in members:
                if member.id == item.id:
                    LOG.info('{} is soft deleting {}', user, item)
                else:
                    LOG.info('Deletion of {} caused deletion of {}', item, member)

                owner = await self._get_cached_user(conn, member.owner_id)
                computed_tags = await self._get_cached_computed_tags(conn, member)
                await self.mediator.tags.save_computed_tags(conn, member, set())
                await self.mediator.tags.decrement_known_tags_user(conn, owner, computed_tags)

                if owner.is_public:
                    await self.mediator.tags.decrement_known_tags_anon(conn, computed_tags)

                for user_id in item.permissions:
                    user = await self._get_cached_user(conn, user_id)
                    await self.mediator.tags.decrement_known_tags_user(conn, user, computed_tags)

                member_metainfo = await self.mediator.meta.get_by_item(conn, member)
                await self.mediator.object_storage.soft_delete(user, owner, member)
                await self.mediator.meta.soft_delete(conn, member_metainfo)
                await self.mediator.items.soft_delete(conn, member)

        return switch_to


class UploadItemUseCase(BaseItemUseCase):
    """Use case for processing image binary content."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        file: models.NewFile,
    ) -> int | None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to upload items')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot upload media to someone else's item")
            now = pu.now()

            oid = None
            content = file.content
            if len(content) >= const.LARGE_OBJECT_SIZE:
                save_content = b''
                oid = await self.mediator.database.save_large_object(content)
                LOG.info('Created large object {} for item {}', oid, item.uuid)
            else:
                save_content = file.content

            operation_id = await self.mediator.misc.save_input_media(
                conn=conn,
                media=models.InputMedia(
                    id=-1,
                    user_uuid=user.uuid,
                    item_uuid=item.uuid,
                    created_at=now,
                    ext='jpg' if file.ext == 'jpeg' else file.ext,
                    content_type=file.content_type,
                    extras={'extract_exif': file.features.extract_exif, 'oid': oid},
                    error=None,
                    content=save_content,
                ),
            )

            await self.mediator.meta.add_item_note(
                conn,
                item=item,
                key='original_filename',
                value=str(file.filename),
            )

            if item.parent_id is not None:
                parent = await self.mediator.items.get_by_id(conn, item.parent_id)
                parent.is_collection = True

                if parent.thumbnail_ext is None:
                    # NOTE - temporarily setting parent metainfo,
                    # so next item in batch will not copy again
                    parent.preview_ext = 'tmp'
                    parent.thumbnail_ext = 'tmp'

                    # TODO - do not save file twice!
                    oid2 = None
                    content = file.content
                    if len(content) >= const.LARGE_OBJECT_SIZE:
                        save_content = b''
                        oid2 = await self.mediator.database.save_large_object(content)
                        LOG.info('Created large object {} for item {}', oid2, parent.uuid)
                    else:
                        save_content = file.content

                    await self.mediator.misc.save_input_media(
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
                                'oid': oid2,
                            },
                            error=None,
                            content=save_content,
                        ),
                    )

                    await self.mediator.meta.add_item_note(
                        conn=conn,
                        item=parent,
                        key='copied_image_from',
                        value=str(item.uuid),
                    )

                await self.mediator.items.save(conn, parent)

        return operation_id


class ChangePermissionsUseCase(BaseItemUseCase):
    """Use case for item permissions change."""

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

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, "You cannot change someone else's item's permissions")

            LOG.info('{} is updating permissions of {}', user, item)

            user_ids: set[int] = set()
            for user_uuid in permissions:
                user = await self.mediator.users.get_by_uuid(conn, user_uuid)
                user_ids.add(user.id)

            if item.permissions == permissions:
                return None

            if apply_to_parents or apply_to_children:
                added, deleted = utils.get_delta(item.permissions, user_ids)

                operation_id = await self.mediator.misc.create_serial_operation(
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
            await self.mediator.items.save(conn, item)

        return operation_id
