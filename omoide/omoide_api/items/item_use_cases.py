"""Use cases for Item-related operations."""

import time
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


class CreateItemsUseCase(BaseItemUseCase):
    """Use case for item creation."""

    async def execute(
        self,
        user: models.User,
        items_in: list[dict[str, Any]],
    ) -> tuple[float, list[models.Item]]:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to='create items')

        start = time.perf_counter()
        items: list[models.Item] = []
        all_affected_users: set[int] = set()

        async with self.mediator.database.transaction() as conn:
            for raw_item in items_in:
                item = await self.create_one_item(conn, user, **raw_item)
                items.append(item)

                all_affected_users.add(item.owner_id)
                all_affected_users.update(item.permissions)

                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    name=const.AllSerialOperations.REBUILD_ITEM_TAGS,
                    extras={
                        'item_id': item.id,
                        'apply_to_children': True,
                        'apply_to_owner': False,
                        'apply_to_permissions': False,
                        'apply_to_anon': False,
                    }
                )

            for user_id in all_affected_users:
                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_USER,
                    extras={'user_id': user_id},
                )

            if user.is_public:
                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_ANON,
                )

        LOG.info(
            'User {} created {} items: {}',
            user,
            len(items),
            sorted(str(item.uuid) for item in items),
        )

        duration = time.perf_counter() - start
        return duration, items


class ReadItemUseCase(BaseAPIUseCase):
    """Use case for item getting."""

    async def execute(self, user: models.User, item_uuid: UUID) -> models.Item:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)

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

        return item


class ReadManyItemsUseCase(BaseAPIUseCase):
    """Use case for item getting."""

    async def execute(
        self,
        user: models.User,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> tuple[float, list[models.Item]]:
        """Execute."""
        start = time.perf_counter()
        async with self.mediator.database.transaction() as conn:
            if user.is_anon:
                items = await self.mediator.items.get_items_anon(
                    conn, owner_uuid, parent_uuid, name, limit
                )
            else:
                items = await self.mediator.items.get_items_known(
                    conn, user, owner_uuid, parent_uuid, name, limit
                )

        duration = time.perf_counter() - start
        return duration, items


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
                name=const.AllSerialOperations.REBUILD_ITEM_TAGS,
                extras={
                    'item_id': item.id,
                    'apply_to_children': True,
                    'apply_to_owner': True,
                    'apply_to_permissions': True,
                    'apply_to_anon': True,
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
                old_parent = None
            else:
                old_parent = await self.mediator.items.get_by_uuid(conn, item.parent_uuid)

            new_parent = await self.mediator.items.get_by_uuid(conn, new_parent_uuid)
            is_child = await self.mediator.items.check_child(conn, new_parent_uuid, item.uuid)

            if is_child:
                msg = 'Item {new_parent_uuid} is actually a child of {item_uuid}'
                raise exceptions.InvalidInputError(
                    msg, new_parent_uuid=new_parent_uuid, item_uuid=item_uuid
                )

            LOG.info(
                '{user} is setting {new_parent} as a parent '
                'for {item} (previous parent is {old_parent})',
                user=user,
                new_parent=new_parent,
                item=item,
                old_parent=old_parent,
            )

            item.parent_uuid = new_parent_uuid
            await self.mediator.items.save(conn, item)

            operation_id_tags = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.REBUILD_ITEM_TAGS,
                extras={
                    'item_id': item.id,
                    'apply_to_children': True,
                    'apply_to_owner': True,
                    'apply_to_permissions': True,
                    'apply_to_anon': True,
                },
            )

            operation_id_old_parent = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_USER,
                extras={'user_id': old_parent.id},
            )

            operation_id_new_parent = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_USER,
                extras={'user_id': new_parent.id},
            )
            # TODO - need to copy image from the item to new parent

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
                name=const.AllSerialOperations.REBUILD_ITEM_TAGS,
                extras={
                    'item_id': item.id,
                    'apply_to_children': True,
                    'apply_to_owner': True,
                    'apply_to_permissions': True,
                    'apply_to_anon': True,
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
        desired_switch: Literal['parent', 'sibling'] | None,
    ) -> models.Item | None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)
        switch_to = None

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

            if item.parent_uuid is None:
                msg = 'Root items cannot be deleted'
                raise exceptions.NotAllowedError(msg)

            if desired_switch == 'parent':
                switch_to = await self.mediator.items.get_by_uuid(conn, item.parent_uuid)

            elif desired_switch == 'sibling':
                siblings = await self.mediator.items.get_siblings(conn, item)
                if len(siblings) > 1:
                    index = siblings.index(item)
                    last = len(siblings) - 1

                    if index == len(siblings) - 1:
                        switch_to = siblings[last - 1]
                    else:
                        switch_to = siblings[index + 1]

            LOG.info('{} is deleting {}', user, item)
            metainfo = await self.mediator.meta.get_by_item(conn, item)
            await self.mediator.object_storage.soft_delete(item)
            await self.mediator.meta.soft_delete(conn, metainfo)
            await self.mediator.items.soft_delete(conn, item)

            members = await self.mediator.items.get_family(conn, item)
            for member in members:
                LOG.warning('Deletion of {} affected {}', item, member)
                member_metainfo = await self.mediator.meta.get_by_item(conn, member)
                await self.mediator.object_storage.soft_delete(member)
                await self.mediator.meta.soft_delete(conn, member_metainfo)
                await self.mediator.items.soft_delete(conn, member)

            await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.DECREASE_ITEM_VISIBILITY,
                extras={'item_id': item.id},
            )

        return switch_to


class BaseUploadUseCase(BaseAPIUseCase):
    """Base class for uploading."""

    media_type: const.MEDIA_TYPE

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        binary_content: bytes,
        ext: str,
    ) -> None:
        """Execute."""
        do_what = f'upload {self.media_type}'
        self.mediator.policy.ensure_registered(user, to=do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=do_what)

            LOG.info('{} is uploading {} for {}', user, self.media_type, item)

            await self.mediator.object_storage.save(
                item=item,
                media_type=self.media_type,
                binary_content=binary_content,
                ext=ext,
            )


class UploadContentForItemUseCase(BaseUploadUseCase):
    """Use case for content uploading."""

    media_type: const.MEDIA_TYPE = const.CONTENT


class UploadPreviewForItemUseCase(BaseUploadUseCase):
    """Use case for preview uploading."""

    media_type: const.MEDIA_TYPE = const.PREVIEW


class UploadThumbnailForItemUseCase(BaseUploadUseCase):
    """Use case for thumbnail uploading."""

    media_type: const.MEDIA_TYPE = const.THUMBNAIL


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
            owner = await self.mediator.users.get_by_uuid(conn, item.owner_uuid)
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
            self.ensure_admin_or_owner(user, item, subject='item permissions')

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
                    name=const.AllSerialOperations.REBUILD_ITEM_PERMISSIONS,
                    extras={
                        'item_id': item.id,
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
