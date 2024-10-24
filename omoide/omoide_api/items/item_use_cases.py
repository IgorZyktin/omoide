"""Use cases for Item-related operations."""

import time
from typing import Any
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
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
        self.ensure_not_anon(user, operation='create items')
        start = time.perf_counter()

        items: list[models.Item] = []
        all_computed_tags: set[str] = set()
        all_affected_users: set[models.User] = set()

        async with self.mediator.storage.transaction():
            for raw_item in items_in:
                item = await self.create_one_item(user, **raw_item)
                items.append(item)

        LOG.info(
            'User {} created {} items: {}',
            user,
            len(items),
            [str(item.uuid) for item in items],
        )

        async with self.mediator.storage.transaction():
            parents: dict[UUID, models.Item] = {}
            for item in items:
                if (
                    item.parent_uuid is not None
                    and item.parent_uuid not in parents
                ):
                    parent = await self.mediator.items_repo.get_item(
                        uuid=item.parent_uuid,
                    )
                    parents[parent.uuid] = parent

            parent_computed_tags: dict[UUID, set[str]] = {}
            for parent in parents.values():
                parent_tags = await self.mediator.misc_repo.get_computed_tags(
                    item=parent,
                )
                parent_computed_tags[parent.uuid] = parent_tags

            for item in items:
                new_users, new_tags = await self.post_item_creation(
                    item=item,
                    parent_computed_tags=parent_computed_tags,
                )
                all_computed_tags.update(new_tags)
                all_affected_users.update(new_users)

        async with self.mediator.storage.transaction():
            for affected_user in all_affected_users:
                await self.mediator.misc_repo.incr_known_tags_known(
                    user=affected_user,
                    tags=all_computed_tags,
                )

            public = await self.mediator.users_repo.get_public_user_uuids()
            users_uuids = {user.uuid for user in all_affected_users}
            anon_affected = users_uuids.intersection(public)

            if anon_affected:
                await self.mediator.misc_repo.incr_known_tags_anon(
                    tags=all_computed_tags,
                )

        duration = time.perf_counter() - start
        return duration, items


class ReadItemUseCase(BaseAPIUseCase):
    """Use case for item getting."""

    async def execute(self, user: models.User, item_uuid: UUID) -> models.Item:
        """Execute."""
        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)

            if any(
                (
                    item.owner_uuid == user.uuid,
                    str(user.uuid) in item.permissions,
                )
            ):
                return item

            public_users = (
                await self.mediator.users_repo.get_public_user_uuids()
            )

            if item.owner_uuid in public_users:
                return item

        # NOTE - hiding the fact
        msg = 'Item {item_uuid} does not exist'
        raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)


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
        async with self.mediator.storage.transaction():
            if user.is_anon:
                items = await self.mediator.items_repo.get_items_anon(
                    owner_uuid, parent_uuid, name, limit
                )
            else:
                items = await self.mediator.items_repo.get_items_known(
                    user, owner_uuid, parent_uuid, name, limit
                )

        duration = time.perf_counter() - start
        return duration, items


class DeleteItemUseCase(BaseItemUseCase):
    """Use case for item deletion."""

    async def execute(self, user: models.User, item_uuid: UUID) -> models.Item:
        """Execute."""
        self.ensure_not_anon(user, operation='delete items')
        repo = self.mediator.misc_repo

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='items')

            if item.parent_uuid is None:
                msg = 'Root items cannot be deleted'
                raise exceptions.NotAllowedError(msg)

            LOG.info('User {} is deleting item {}', user, item)

            siblings = await self.mediator.items_repo.get_siblings(item)

            if len(siblings) > 1:
                index = siblings.index(item)
                last = len(siblings) - 1

                if index == len(siblings) - 1:
                    switch_to = siblings[last - 1]
                else:
                    switch_to = siblings[index + 1]

            else:
                switch_to = await self.mediator.items_repo.get_item(
                    uuid=item.parent_uuid,
                )

        # TODO - put it into long job
        affected_users: dict[UUID, models.User] = {user.uuid: user}
        computed_tags: set[str] = set()
        async with self.mediator.storage.transaction():
            # heavy recursive call
            await self.delete_one_item(item, affected_users, computed_tags)

        async with self.mediator.storage.transaction():
            public = await self.mediator.users_repo.get_public_user_uuids()
            users_uuids = set(affected_users.keys())
            anon_affected = users_uuids.intersection(public)

            if anon_affected:
                await repo.decr_known_tags_anon(computed_tags)
                await repo.drop_unused_known_tags_anon()

            for affected_user in affected_users.values():
                await repo.decr_known_tags_known(
                    user=affected_user,
                    tags=computed_tags,
                )
                await repo.drop_unused_known_tags_known(affected_user)

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
        self.ensure_not_anon(user, operation=f'upload {self.media_type}')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(
                user, item, subject=f'item {self.media_type} data'
            )

            LOG.info(
                'User {} is uploading {} for item {}',
                user,
                self.media_type,
                item,
            )

            await self.mediator.object_storage.save_object(
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

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            owner = await self.mediator.users_repo.get_user_by_uuid(
                item.owner_uuid
            )
            public_users = (
                await self.mediator.users_repo.get_public_user_uuids()
            )

            if all(
                (
                    owner.uuid not in public_users,
                    user.uuid != owner.uuid,
                    user.uuid not in item.permissions,
                )
            ):
                # NOTE - hiding the fact
                msg = 'Item {item_uuid} does not exist'
                raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

            children = await self.mediator.items_repo.get_children(item)
            signatures = (
                await self.mediator.signatures_repo.get_cr32_signatures(
                    items=children,
                )
            )
            metainfos = await self.mediator.meta_repo.get_metainfos(children)
            valid_children = [
                child
                for child in children
                if child.content_ext is not None and not child.is_collection
            ]

            total = len(valid_children)
            for i, child in enumerate(valid_children, start=1):
                signature = signatures.get(child.id)
                metainfo = metainfos.get(child.uuid)  # TODO - use item.id

                if signature is None:
                    LOG.warning(
                        'User {} requested download '
                        'for item {}, but is has no signature',
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

        user_visible_filename = (
            f'{template.format(current)}___{item_uuid}.{content_ext}'
        )

        if signature is None:
            checksum = '-'
        else:
            # hash must be converted 123 -> '0x7b' -> '7b
            checksum = hex(signature)[2:]

        size = 0
        if metainfo and metainfo.content_size is not None:
            size = metainfo.content_size

        return f'{checksum} {size} {fs_path} {user_visible_filename}'
