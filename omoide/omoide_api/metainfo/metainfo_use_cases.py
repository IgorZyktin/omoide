"""Use cases for Metainfo-related operations."""
from uuid import UUID

from omoide import models
from omoide import utils
from omoide import custom_logging
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class ReadMetainfoUseCase(BaseAPIUseCase):
    """Use case for getting Metainfo."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> models.Metainfo:
        """Execute."""
        self.ensure_not_anon(user, operation='read metainfo records')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner_or_allowed_to(user, item,
                                                     subject='item metadata')

            metainfo = await self.mediator.meta_repo.read_metainfo(item_uuid)

        return metainfo


class UpdateMetainfoUseCase(BaseAPIUseCase):
    """Use case for updating Metainfo."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        metainfo: models.Metainfo,
    ) -> None:
        """Execute."""
        self.ensure_not_anon(user, operation='update metainfo records')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='item metadata')

            LOG.info('Updating metainfo for {}, command by {}', item, user)

            current_metainfo = await self.mediator.meta_repo.read_metainfo(
                item_uuid
            )

            current_metainfo.updated_at = utils.now()

            current_metainfo.user_time = metainfo.user_time
            current_metainfo.content_type = metainfo.content_type

            current_metainfo.author = metainfo.author
            current_metainfo.author_url = metainfo.author_url
            current_metainfo.saved_from_url = metainfo.saved_from_url
            current_metainfo.description = metainfo.description
            current_metainfo.extras = metainfo.extras

            current_metainfo.content_size = metainfo.content_size
            current_metainfo.preview_size = metainfo.preview_size
            current_metainfo.thumbnail_size = metainfo.thumbnail_size

            current_metainfo.content_width = metainfo.content_width
            current_metainfo.content_height = metainfo.content_height
            current_metainfo.preview_width = metainfo.preview_width
            current_metainfo.preview_height = metainfo.preview_height
            current_metainfo.thumbnail_width = metainfo.thumbnail_width
            current_metainfo.thumbnail_height = metainfo.thumbnail_height

            await self.mediator.meta_repo.update_metainfo(user,
                                                          item_uuid,
                                                          current_metainfo)
