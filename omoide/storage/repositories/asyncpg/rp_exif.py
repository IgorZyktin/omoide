"""Repository that performs CRUD operations on EXIF.
"""
from uuid import UUID

import sqlalchemy as sa
from asyncpg import exceptions as asyncpg_exceptions

from omoide.domain import exceptions
from omoide.domain.core import core_models
from omoide.domain.storage.interfaces.in_rp_exif import AbsEXIFRepository
from omoide.infra import custom_logging
from omoide.storage.database import db_models

LOG = custom_logging.get_logger(__name__)


class EXIFRepository(AbsEXIFRepository):
    """Repository that performs CRUD operations on EXIF."""

    async def create_exif(self, exif: core_models.EXIF) -> core_models.EXIF:
        """Create EXIF."""
        stmt = sa.insert(
            db_models.EXIF
        ).values(
            item_uuid=exif.item_uuid,
            exif=exif.exif,
        )

        try:
            await self.db.execute(stmt)
        except asyncpg_exceptions.UniqueViolationError as exc:
            raise exceptions.EXIFAlreadyExistError(
                item_uuid=exif.item_uuid,
            ) from exc
        else:
            result = exif

        return result

    async def update_exif(self, exif: core_models.EXIF) -> core_models.EXIF:
        """Update EXIF."""
        stmt = sa.update(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == exif.item_uuid
        ).values(
            exif=exif.exif,
        ).returning(1)

        response = await self.db.fetch_one(stmt)

        if response is None:
            raise exceptions.EXIFDoesNotExistError(item_uuid=exif.item_uuid)

        return exif

    async def get_exif_by_item_uuid(self, item_uuid: UUID) -> core_models.EXIF:
        """Return EXIF."""
        stmt = sa.select(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == item_uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            raise exceptions.EXIFDoesNotExistError(item_uuid=item_uuid)

        return core_models.EXIF(
            item_uuid=response['item_uuid'],
            exif=response['exif'],
        )

    async def delete_exif(self, item_uuid: UUID) -> None:
        """Delete EXIF."""
        stmt = sa.delete(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == item_uuid
        ).returning(1)

        response = await self.db.fetch_one(stmt)

        if response is None:
            raise exceptions.EXIFDoesNotExistError(item_uuid=item_uuid)

        return None
