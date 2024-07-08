"""Use cases for Metainfo."""
from uuid import UUID

from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.domain import Item  # FIXME - import from models
from omoide.infra import custom_logging
from omoide.omoide_api.common.use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class BaseMetainfoUseCase(BaseAPIUseCase):
    """Base class for metainfo-related use cases."""

    async def _get_item(self, item_uuid: UUID) -> Item:
        """Generic checks before work."""
        # FEATURE - raise right from repository
        item = await self.mediator.items_repo.read_item(item_uuid)

        if item is None:
            msg = 'Item with UUID {uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, uuid=item_uuid)

        return item


class ReadMetainfoUseCase(BaseMetainfoUseCase):
    """Use case for getting Metainfo."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> models.Metainfo:
        self.ensure_not_anon(user, target='read metainfo records')

        async with self.mediator.storage.transaction():
            item = await self._get_item(item_uuid)

            if (
                item.owner_uuid != user.uuid
                and str(user.uuid) not in item.permissions
                and not user.is_admin
            ):
                msg = (
                    'You are not allowed to perform '
                    'such operation with item metadata'
                )
                raise exceptions.AccessDeniedError(msg, uuid=item_uuid)

            metainfo = await self.mediator.meta_repo.read_metainfo(item_uuid)

        return metainfo


class UpdateMetainfoUseCase(BaseMetainfoUseCase):
    """Use case for updating Metainfo."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        metainfo: models.Metainfo,
    ) -> None:
        """Business logic."""
        LOG.info('Updating metainfo for item {}, command by user {}',
                 item_uuid, user.uuid)

        self.ensure_not_anon(user, target='update metainfo records')

        async with self.mediator.storage.transaction():
            item = await self._get_item(item_uuid)

            if item.owner_uuid != user.uuid and not user.is_admin:
                msg = (
                    'You are not allowed to perform '
                    'such operation with item metadata'
                )
                raise exceptions.AccessDeniedError(msg, uuid=item_uuid)

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
