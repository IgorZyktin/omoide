"""Use cases for Metainfo-related operations."""

from uuid import UUID

from omoide import custom_logging
from omoide import models
from omoide import utils
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

        async with self.mediator.database.transaction():
            item = await self.mediator.items.get_item(item_uuid)
            self.ensure_admin_or_owner_or_allowed_to(
                user, item, subject='item metadata'
            )

            metainfo = await self.mediator.meta.read_metainfo(item)

        return metainfo


class UpdateMetainfoUseCase(BaseAPIUseCase):
    """Use case for updating Metainfo."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        metainfo: models.MetainfoOld,
    ) -> None:
        """Execute."""
        self.ensure_not_anon(user, operation='update metainfo records')

        async with self.mediator.database.transaction():
            item = await self.mediator.items.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='item metadata')

            LOG.info('Updating metainfo for {}, command by {}', item, user)

            current_metainfo = await self.mediator.meta.read_metainfo(
                item
            )

            current_metainfo.updated_at = utils.now()

            current_metainfo.user_time = metainfo.user_time
            current_metainfo.content_type = metainfo.content_type

            current_metainfo.content_width = metainfo.content_width
            current_metainfo.content_height = metainfo.content_height

            current_metainfo.preview_width = metainfo.preview_width
            current_metainfo.preview_height = metainfo.preview_height

            current_metainfo.thumbnail_width = metainfo.thumbnail_width
            current_metainfo.thumbnail_height = metainfo.thumbnail_height

            await self.mediator.meta.update_metainfo(
                item_uuid, current_metainfo
            )
