"""Use cases for Metainfo-related operations."""

from uuid import UUID

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
