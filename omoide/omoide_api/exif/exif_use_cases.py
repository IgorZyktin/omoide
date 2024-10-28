"""Use cases for EXIF-related operations."""

from typing import Any
from uuid import UUID

from omoide import custom_logging
from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class CreateEXIFUseCase(BaseAPIUseCase):
    """Use case for creation of an EXIF."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        exif: dict[str, Any],
    ) -> None:
        """Execute."""
        self.ensure_not_anon(user, operation='add EXIF data')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='EXIF data')

            LOG.info('{} is creating EXIF for {}', user, item)
            await self.mediator.exif.create(conn, item, exif)


class ReadEXIFUseCase(BaseAPIUseCase):
    """Use case for getting an EXIF."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> dict[str, Any]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_item(item_uuid)
            self.ensure_admin_or_owner_or_allowed_to(user, item, subject='EXIF data')

            exif = await self.mediator.exif.get_by_item(conn, item)

        return exif


class UpdateEXIFUseCase(BaseAPIUseCase):
    """Use case for updating of an EXIF."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        exif: dict[str, Any],
    ) -> None:
        """Execute."""
        self.ensure_not_anon(user, operation='update EXIF data')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.ensure_admin_or_owner(user, item, subject='EXIF data')

            LOG.info('{} is updating EXIF for {}', user, item)
            await self.mediator.exif.save(conn, item, exif)


class DeleteEXIFUseCase(BaseAPIUseCase):
    """Use case for deleting of an EXIF."""

    async def execute(self, user: models.User, item_uuid: UUID) -> None:
        """Execute."""
        self.ensure_not_anon(user, operation='delete EXIF data')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            self.ensure_admin_or_owner(user, item, subject='EXIF data')

            LOG.info('{} is deleting EXIF for {}', user, item)
            await self.mediator.exif.delete(conn, item)
