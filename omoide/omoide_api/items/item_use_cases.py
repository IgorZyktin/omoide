"""Use cases for Item-related operations."""

from typing import Any
from typing import Literal
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase
from omoide.omoide_api.common.common_use_cases import BaseItemUseCase

LOG = custom_logging.get_logger(__name__)


class CreateManyItemsUseCase(BaseItemUseCase):
    """Use case for item creation."""

    do_what: str = 'create items'

    async def execute(
        self,
        user: models.User,
        *items_in: dict[str, Any],
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        items: list[models.Item] = []
        users_map: dict[int, models.User | None] = {user.id: user}

        async with self.mediator.database.transaction() as conn:
            for raw_item in items_in:
                item = await self.create_one_item(conn, user, **raw_item)
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


class GetManyItemsUseCase(BaseAPIUseCase):
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

    do_what: str = 'update items'

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        is_collection: bool,
    ) -> None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

            if item.is_collection == is_collection:
                return

            LOG.info('{} is updating {}', user, item)

            item.is_collection = is_collection
            await self.mediator.items.save(conn, item)


class RenameItemUseCase(BaseItemUseCase):
    """Use case for item rename."""

    do_what: str = 'rename items'

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        name: str,
    ) -> int | None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

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

    do_what: str = 'change item parent'

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        new_parent_uuid: UUID,
    ) -> list[int]:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

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

        if new_parent.has_incomplete_media():
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

    do_what: str = 'change item tags'

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        tags: set[str],
    ) -> int | None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

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

    do_what: str = 'delete items'

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        desired_switch: Literal['parent', 'sibling'],
    ) -> models.Item | None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)
        switch_to = None

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

            if item.parent_uuid is None:
                LOG.warning('{} tried to delete root {}', user, item)
                msg = 'Root items cannot be deleted'
                raise exceptions.NotAllowedError(msg)

            if desired_switch == 'sibling':
                siblings = await self.mediator.items.get_siblings(conn, item)
                if len(siblings) > 1:
                    index = siblings.index(item)
                    last = len(siblings) - 1

                    if index == len(siblings) - 1:
                        switch_to = siblings[last - 1]
                    else:
                        switch_to = siblings[index + 1]

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


class UploadItemUseCase(BaseAPIUseCase):
    """Use case for processing image binary content."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        file: models.NewFile,
    ) -> int | None:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to='upload media to this item')

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name='upload',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(item.uuid),
                    'content_type': file.content_type,
                    'filename': file.filename,
                    'ext': file.ext,
                    'features': {
                        'extract_exif': file.features.extract_exif,
                        'last_modified': (
                            file.features.last_modified.isoformat()
                            if file.features.last_modified
                            else None
                        ),
                    },
                },
                payload=file.content,
            )

            owner = await self.mediator.users.get_by_id(conn, item.owner_id)

            parent = None
            if item.parent_id is not None:
                parent = await self.mediator.items.get_by_id(conn, item.parent_id)

        if parent is not None and parent.has_incomplete_media():
            media_types = await self.mediator.object_storage.copy_all_objects(
                requested_by=user,
                owner=owner,
                source_item=item,
                target_item=parent,
            )

            if media_types:
                async with self.mediator.database.transaction() as conn:
                    await self.mediator.meta.add_item_note(
                        conn=conn,
                        item=parent,
                        key='copied_image_from',
                        value=str(item.uuid),
                    )

        return operation_id


class DownloadCollectionUseCase(BaseItemUseCase):
    """Use case for downloading whole group of items as zip archive."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> tuple[list[str], models.User, models.Item | None]:
        """Execute."""
        lines: list[str] = []

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)
            public_users = await self.mediator.users.get_public_user_ids(conn)

            if all(
                (
                    owner.id not in public_users,
                    user.id != owner.id,
                    user.id not in item.permissions,
                )
            ):
                # NOTE - hiding the fact
                msg = 'Item {item_uuid} does not exist'
                raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

            children = await self.mediator.items.get_children(conn, item)

        # TODO - remove transaction splitting
        async with self.mediator.database.transaction() as conn:
            signatures = await self.mediator.signatures.get_cr32_signatures_map(
                conn=conn,
                items=children,
            )

        async with self.mediator.database.transaction() as conn:
            metainfos = await self.mediator.meta.get_metainfo_map(conn, children)
            valid_children = [
                child
                for child in children
                if child.content_ext is not None and not child.is_collection
            ]

            total = len(valid_children)
            for i, child in enumerate(valid_children, start=1):
                signature = signatures.get(child.id)
                metainfo = metainfos.get(child.id)

                if signature is None:
                    LOG.warning(
                        'User {} requested download for item {}, but is has no signature',
                        user,
                        item,
                    )

                lines.append(
                    self.form_signature_line(
                        item=child,
                        metainfo=metainfo,
                        signature=signature,
                        current=i,
                        total=total,
                    )
                )

        return lines, owner, item

    @staticmethod
    def form_signature_line(
        item: models.Item,
        metainfo: models.Metainfo | None,
        signature: int | None,
        current: int,
        total: int,
    ) -> str:
        """Generate signature line for NGINX.

        Example:
        (
            '2caf75ed '
            + '16948 '
            + '/content/content/92b0f.../14/14e0bc....jpg '
            + '7___14e0bc49-8561-4667-8210-202e1965b499.jpg'
        )

        """
        digits = len(str(total))
        template = f'{{:0{digits}d}}'
        owner_uuid = str(item.owner_uuid)
        item_uuid = str(item.uuid)
        base = '/content/content'  # TODO - ensure it is correct path
        prefix = item_uuid[: const.STORAGE_PREFIX_SIZE]
        content_ext = str(item.content_ext)

        fs_path = f'{base}/{owner_uuid}/{prefix}/{item_uuid}.{content_ext}'

        user_visible_filename = f'{template.format(current)}___{item_uuid}.{content_ext}'

        if signature is None:
            checksum = '-'
        else:
            # hash must be converted 123 -> '0x7b' -> '7b
            checksum = hex(signature)[2:]

        size = 0
        if metainfo and metainfo.content_size is not None:
            size = metainfo.content_size

        return f'{checksum} {size} {fs_path} {user_visible_filename}'


class ChangePermissionsUseCase(BaseAPIUseCase):
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
        operation_id = None

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_can_change(user, item, to='change item permissions')

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
