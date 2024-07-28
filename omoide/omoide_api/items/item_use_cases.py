"""Use cases for Item-related operations."""
from uuid import UUID

from omoide import exceptions
from omoide import models
from omoide import utils
from omoide import custom_logging
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


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
                owner = await self.mediator.users_repo.read_user(
                    uuid=item.owner_uuid,
                )
                affected_users.append(owner)
            else:
                affected_users.append(user)

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

            parent_uuid = item.parent_uuid
            await self.mediator.items_repo.delete_item(item_uuid)

        return parent_uuid


class UploadContentForItemUseCase(BaseAPIUseCase):
    """Use case for content uploading."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        raw_media: models.RawMedia,
    ) -> int:
        """Execute."""
        self.ensure_not_anon(user, operation='upload item media data')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='item media data')

            LOG.info('User {} is uploading content for item {}', user, item)

            media = models.Media(
                id=-1,
                created_at=utils.now(),
                processed_at=None,
                error=None,
                owner_uuid=user.uuid,
                item_uuid=item_uuid,
                media_type=raw_media.media_type,
                content=raw_media.content,
                ext=raw_media.ext,
            )

            media_id = await self.mediator.media_repo.create_media(media)

        return media_id


class UploadPreviewForItemUseCase(BaseAPIUseCase):
    """Use case for preview uploading."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        raw_media: models.RawMedia,
    ) -> int:
        """Execute."""
        self.ensure_not_anon(user, operation='upload item media data')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='item media data')

            LOG.info('User {} is uploading preview for item {}', user, item)

            media = models.Media(
                id=-1,
                created_at=utils.now(),
                processed_at=None,
                error=None,
                owner_uuid=user.uuid,
                item_uuid=item_uuid,
                media_type=raw_media.media_type,
                content=raw_media.content,
                ext=raw_media.ext,
            )

            media_id = await self.mediator.media_repo.create_media(media)

        return media_id


class UploadThumbnailForItemUseCase(BaseAPIUseCase):
    """Use case for thumbnail uploading."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        raw_media: models.RawMedia,
    ) -> int:
        """Execute."""
        self.ensure_not_anon(user, operation='upload item media data')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='item media data')

            LOG.info('User {} is uploading thumbnail for item {}', user, item)

            media = models.Media(
                id=-1,
                created_at=utils.now(),
                processed_at=None,
                error=None,
                owner_uuid=user.uuid,
                item_uuid=item_uuid,
                media_type=raw_media.media_type,
                content=raw_media.content,
                ext=raw_media.ext,
            )

            media_id = await self.mediator.media_repo.create_media(media)

        return media_id
