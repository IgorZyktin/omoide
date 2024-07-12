"""Use cases for Media-related operations."""
from uuid import UUID

from omoide import models
from omoide import utils
from omoide.infra import custom_logging
from omoide.omoide_api.common.use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class CreateMediaUseCase(BaseAPIUseCase):
    """Use case for creation of a media."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        raw_media: models.RawMedia,
    ) -> int:
        """Execute."""
        self.ensure_not_anon(user, operation='add media data')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='item media data')

            LOG.info('Creating media for {}, command by {}', item, user)

            media = models.Media(
                id=-1,
                created_at=utils.now(),
                processed_at=None,
                error=None,
                owner_uuid=user.uuid,
                item_uuid=item_uuid,
                **raw_media.model_dump(),
            )

            # TODO - fix naming
            media_id = await self.mediator.media_repo.create_media2(media)

        return media_id
