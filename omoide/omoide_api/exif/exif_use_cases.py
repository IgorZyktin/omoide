"""Use cases for EXIF-related operations."""

from typing import Any
from uuid import UUID

from omoide import custom_logging
from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class CreateEXIFUseCase(BaseAPIUseCase):
    """Use case for creation of an EXIF."""

    do_what: str = 'create EXIF data'

    async def execute(self, user: models.User, item_uuid: UUID, exif: dict[str, Any]) -> None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

            LOG.info('{} is creating EXIF for {}', user, item)
            await self.mediator.exif.create(conn, item, exif)


class ReadEXIFUseCase(BaseAPIUseCase):
    """Use case for getting an EXIF."""

    do_what: str = 'read EXIF data'

    async def execute(self, user: models.User, item_uuid: UUID) -> dict[str, Any]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_can_see(user, item, to=self.do_what)

            exif = await self.mediator.exif.get_by_item(conn, item)

        return exif


class UpdateEXIFUseCase(BaseAPIUseCase):
    """Use case for updating of an EXIF."""

    do_what: str = 'update EXIF data'

    async def execute(self, user: models.User, item_uuid: UUID, exif: dict[str, Any]) -> None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

            LOG.info('{} is updating EXIF for {}', user, item)
            await self.mediator.exif.save(conn, item, exif)


class DeleteEXIFUseCase(BaseAPIUseCase):
    """Use case for deleting of an EXIF."""

    do_what: str = 'delete EXIF data'

    async def execute(self, user: models.User, item_uuid: UUID) -> None:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.mediator.policy.ensure_owner(user, item, to=self.do_what)

            LOG.info('{} is deleting EXIF for {}', user, item)
            await self.mediator.exif.delete(conn, item)
