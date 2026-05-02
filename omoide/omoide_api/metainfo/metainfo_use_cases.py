"""Use cases for Metainfo-related operations."""

from datetime import datetime
from typing import Any
from uuid import UUID

import python_utilz as pu

from omoide import custom_logging
from omoide import models
from omoide.domain import ensure
from omoide.infra import mediators

LOG = custom_logging.get_logger(__name__)


class BaseMetainfoUseCase:
    """Base use case class."""

    def __init__(self, mediator: mediators.MetainfoMediator) -> None:
        """Initialize instance."""
        self.mediator = mediator


class ReadMetainfoUseCase(BaseMetainfoUseCase):
    """Use case for getting Metainfo."""

    async def execute(self, user: models.User, item_uuid: UUID) -> models.Metainfo:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.can_see(
                user,
                item,
                f'You are not allowed to see item {item_uuid} and its metadata',
            )

            metainfo = await self.mediator.meta.get_by_item(conn, item)

        return metainfo


class UpdateMetainfoUseCase(BaseMetainfoUseCase):
    """Use case for updating Metainfo."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        user_time: datetime | None,
        content_type: str | None,
        extras: dict[str, Any],
    ) -> None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to update item metadata')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            ensure.owner(
                user,
                item,
                f'You must own item {item_uuid} to update its metadata',
            )

            LOG.info('{} is updating metainfo for {}', user, item)
            metainfo = await self.mediator.meta.get_by_item(conn, item)

            metainfo.updated_at = pu.now()
            metainfo.user_time = user_time
            metainfo.content_type = content_type
            await self.mediator.meta.save(conn, metainfo)

            for key, value in extras.items():
                await self.mediator.meta.add_item_note(conn, item, key, value)
