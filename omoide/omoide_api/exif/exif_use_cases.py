"""Use cases for EXIF-related operations."""
from typing import Any
from uuid import UUID

from omoide import models
from omoide.infra import custom_logging
from omoide.omoide_api.common.use_cases import BaseAPIUseCase

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

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='EXIF data')

            LOG.info('Creating EXIF for {}, command by {}', item, user)
            await self.mediator.exif_repo.create_exif(item_uuid, exif)


class ReadEXIFUseCase(BaseAPIUseCase):
    """Use case for getting an EXIF."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> dict[str, Any]:
        """Execute."""
        self.ensure_not_anon(user, operation='read EXIF data')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_allowed_to(user, item, subject='EXIF data')
            exif = await self.mediator.exif_repo.read_exif(item_uuid)

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

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='EXIF data')

            LOG.info('Updating EXIF for {}, command by {}', item, user)
            await self.mediator.exif_repo.update_exif(item_uuid, exif)


class DeleteEXIFUseCase(BaseAPIUseCase):
    """Use case for deleting of an EXIF."""

    async def execute(self, user: models.User, item_uuid: UUID) -> None:
        """Execute."""
        self.ensure_not_anon(user, operation='delete EXIF data')

        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            self.ensure_admin_or_owner(user, item, subject='EXIF data')

            LOG.info('Deleting EXIF for {}, command by {}', item, user)
            await self.mediator.exif_repo.delete_exif(item_uuid)