"""Use cases for Item-related operations."""
from uuid import UUID

from omoide import models
from omoide import utils
from omoide.infra import custom_logging
from omoide.omoide_api.common.use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


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
                **raw_media.model_dump(),
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
                **raw_media.model_dump(),
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
                **raw_media.model_dump(),
            )

            media_id = await self.mediator.media_repo.create_media(media)

        return media_id
