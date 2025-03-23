"""Use cases for Metainfo-related operations."""

from datetime import datetime
from typing import Any
from uuid import UUID

import python_utilz as pu

from omoide import custom_logging
from omoide import models
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

    do_what: str = 'update metainfo'

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        user_time: datetime | None,
        content_type: str | None,
        extras: dict[str, Any],
    ) -> None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

            LOG.info('{} is updating metainfo for {}', user, item)
            metainfo = await self.mediator.meta.get_by_item(conn, item)

            metainfo.updated_at = pu.now()
            metainfo.user_time = user_time
            metainfo.content_type = content_type
            await self.mediator.meta.save(conn, metainfo)

            for key, value in extras.items():
                await self.mediator.meta.add_item_note(conn, item, key, value)
