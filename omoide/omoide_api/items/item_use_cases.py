"""Use cases for Item-related operations."""
from uuid import UUID

from omoide import const
from omoide import exceptions
from omoide import models
from omoide import custom_logging
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


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
                await self.mediator.users_repo.get_public_users_uuids()
            )

            if item.owner_uuid in public_users:
                return item

        # NOTE - hiding the fact
        msg = 'Item {item_uuid} does not exist'
        raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)


class DeleteItemUseCase(BaseAPIUseCase):
    """Use case for item deletion."""

    async def execute(self, user: models.User, item_uuid: UUID) -> UUID:
        """Execute."""
        self.ensure_not_anon(user, operation='delete items')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='items')

            if item.parent_uuid is None:
                msg = 'Root items cannot be deleted'
                raise exceptions.NotAllowedError(msg)

            LOG.info('User {} is deleting item {}', user, item)

            affected_users = []
            if item.owner_uuid != user.uuid:
                owner = await self.mediator.users_repo.get_user(
                    uuid=item.owner_uuid,
                )
                affected_users.append(owner)
            else:
                affected_users.append(user)

            # TODO - what about child items? They also can have lots of tags
            await self.mediator.misc_repo.update_known_tags(
                users=affected_users,
                tags_added=[],
                tags_deleted=item.tags,
            )

            public_users = (
                await self.mediator.users_repo.get_public_users_uuids()
            )
            await self.mediator.misc_repo.drop_unused_known_tags(
                users=affected_users,
                public_users=public_users,
            )

            # TODO - what about child items? They also can have lots of objects
            await self.mediator.object_storage.delete_all_objects(item)

            parent_uuid = item.parent_uuid
            await self.mediator.items_repo.delete_item(item_uuid)

        return parent_uuid


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
            self.ensure_admin_or_owner(user, item,
                                       subject=f'item {self.media_type} data')

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
