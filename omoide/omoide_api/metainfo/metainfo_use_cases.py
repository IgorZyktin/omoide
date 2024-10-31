"""Use cases for Metainfo-related operations."""

from datetime import datetime
from typing import Any
from uuid import UUID

from omoide import custom_logging
from omoide import models
from omoide import utils
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class ReadMetainfoUseCase(BaseAPIUseCase):
    """Use case for getting Metainfo."""

    do_what: str = 'read metainfo'

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> models.Metainfo:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_can_see(user, item, to=self.do_what)

            metainfo = await self.mediator.meta.get_by_item(conn, item)

        return metainfo


class UpdateMetainfoUseCase(BaseAPIUseCase):
    """Use case for updating Metainfo."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        user_time: datetime | None,
        content_type: str | None,
        extras: dict[str, Any],
        content_width: int | None,
        content_height: int | None,
        preview_width: int | None,
        preview_height: int | None,
        thumbnail_width: int | None,
        thumbnail_height: int | None,
    ) -> None:
        """Execute."""
        self.ensure_not_anon(user, operation='update metainfo records')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.ensure_admin_or_owner(user, item, subject='item metadata')

            LOG.info('Updating metainfo for {}, command by {}', item, user)

            metainfo = await self.mediator.meta.get_by_item(conn, item)

            metainfo.updated_at = utils.now()

            metainfo.user_time = user_time
            metainfo.content_type = content_type

            metainfo.content_width = content_width
            metainfo.content_height = content_height

            metainfo.preview_width = preview_width
            metainfo.preview_height = preview_height

            metainfo.thumbnail_width = thumbnail_width
            metainfo.thumbnail_height = thumbnail_height

            await self.mediator.meta.save(conn, metainfo)

            for key, value in extras.items():
                await self.mediator.meta.add_item_note(conn, item, key, value)
