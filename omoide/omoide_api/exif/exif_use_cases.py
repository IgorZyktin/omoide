"""Use cases for EXIF-related operations."""
from typing import Any
from uuid import UUID

from omoide import exceptions
from omoide import models
from omoide.domain import Item  # FIXME - import from models
from omoide.infra import custom_logging
from omoide.omoide_api.common.use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class BaseEXIFsUseCase(BaseAPIUseCase):
    """Base class for exif-related use cases."""

    async def _get_item(self, item_uuid: UUID) -> Item:
        """Generic checks before work."""
        # FEATURE - raise right from repository
        item = await self.mediator.items_repo.read_item(item_uuid)

        if item is None:
            msg = 'Item with UUID {uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, uuid=item_uuid)

        return item


class CreateEXIFUseCase(BaseEXIFsUseCase):
    """Use case for creation of an EXIF."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        exif: dict[str, Any],
    ) -> None:
        """Execute."""
        LOG.info('Creating EXIF for item {}, command by user {}',
                 item_uuid, user.uuid)
        self.ensure_not_anon(user, target='add EXIF data')

        async with self.mediator.storage.transaction():
            item = await self._get_item(item_uuid)

            if item.owner_uuid != user.uuid:
                msg = (
                    'You are not allowed to perform '
                    'such operation with EXIF data'
                )
                raise exceptions.AccessDeniedError(msg)

            await self.mediator.exif_repo.create_exif(item_uuid, exif)


class ReadEXIFUseCase(BaseEXIFsUseCase):
    """Use case for getting an EXIF."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> dict[str, Any]:
        """Execute."""
        self.ensure_not_anon(user, target='read EXIF data')

        async with self.mediator.storage.transaction():
            item = await self._get_item(item_uuid)

            if (
                item.owner_uuid != user.uuid
                and str(user.uuid) not in item.permissions
                and not user.is_admin
            ):
                msg = (
                    'You are not allowed to perform '
                    'such operation with EXIF data'
                )
                raise exceptions.AccessDeniedError(msg)

            exif = await self.mediator.exif_repo.read_exif(item_uuid)

        return exif


class UpdateEXIFUseCase(BaseEXIFsUseCase):
    """Use case for updating of an EXIF."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        exif: dict[str, Any],
    ) -> None:
        """Execute."""
        LOG.info('Updating EXIF for item {}, command by user {}',
                 item_uuid, user.uuid)

        self.ensure_not_anon(user, target='update EXIF data')

        async with self.mediator.storage.transaction():
            item = await self._get_item(item_uuid)

            if item.owner_uuid != user.uuid and not user.is_admin:
                msg = (
                    'You are not allowed to perform '
                    'such operation with EXIF data'
                )
                raise exceptions.AccessDeniedError(msg)

            await self.mediator.exif_repo.update_exif(item_uuid, exif)


class DeleteEXIFUseCase(BaseEXIFsUseCase):
    """Use case for deleting of an EXIF."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> None:
        """Execute."""
        LOG.info('Dropping EXIF for item {}, command by user {}',
                 item_uuid, user.uuid)

        self.ensure_not_anon(user, target='delete EXIF data')

        async with self.mediator.storage.transaction():
            item = await self._get_item(item_uuid)

            if item.owner_uuid != user.uuid and not user.is_admin:
                msg = (
                    'You are not allowed to perform '
                    'such operation with EXIF data'
                )
                raise exceptions.AccessDeniedError(msg)

            await self.mediator.exif_repo.delete_exif(item_uuid)
