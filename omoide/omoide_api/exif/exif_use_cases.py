"""Use cases for EXIF-related operations."""

from uuid import UUID

from omoide import custom_logging
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.domain import ensure

LOG = custom_logging.get_logger(__name__)


class BaseEXIFUseCase:
    """Base use case class."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        exif: db_interfaces.AbsEXIFRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items
        self.exif = exif


class CreateEXIFUseCase(BaseEXIFUseCase):
    """Add EXIF data to existing item."""

    async def execute(self, user: models.User, item_uuid: UUID, exif: models.Exif) -> None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to create EXIF data')

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(user, item, f'You must own item {item_uuid} to create EXIF data for it')

            LOG.info('{} is creating EXIF for {}', user, item)
            await self.exif.create(conn, item, exif)


class ReadEXIFUseCase(BaseEXIFUseCase):
    """Read EXIF data for existing item."""

    async def execute(self, user: models.User, item_uuid: UUID) -> models.Exif:
        """Execute."""
        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.can_see(
                user,
                item,
                f'You are not allowed to see item {item_uuid} and its EXIF data',
            )

            exif = await self.exif.get_by_item(conn, item)

        return exif


class UpdateEXIFUseCase(BaseEXIFUseCase):
    """Update EXIF data for existing item.

    If item has no EXIF data at the moment, it will be created.
    """

    async def execute(self, user: models.User, item_uuid: UUID, exif: models.Exif) -> None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to update EXIF data')

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(
                user,
                item,
                f'You must own item {item_uuid} to update its EXIF data',
            )

            LOG.info('{} is updating EXIF for {}', user, item)
            await self.exif.save(conn, item, exif)


class DeleteEXIFUseCase(BaseEXIFUseCase):
    """Use case for deleting of an EXIF."""

    async def execute(self, user: models.User, item_uuid: UUID) -> None:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to delete EXIF data')

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            ensure.owner(
                user,
                item,
                f'You must own item {item_uuid} to delete its EXIF data',
            )

            LOG.info('{} is deleting EXIF for {}', user, item)
            await self.exif.delete(conn, item)
