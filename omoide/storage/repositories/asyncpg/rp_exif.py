"""Repository that performs CRUD operations on EXIF."""
from uuid import UUID

import sqlalchemy as sa
from asyncpg import exceptions as asyncpg_exceptions
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import exceptions
from omoide.storage import interfaces
from omoide.storage.asyncpg_storage import AsyncpgStorage
from omoide.storage.database import db_models


class EXIFRepository(interfaces.AbsEXIFRepository, AsyncpgStorage):
    """Repository that performs CRUD operations on EXIF."""

    async def create_exif(self, item_uuid: UUID, exif: dict[str, str]) -> None:
        """Create EXIF."""
        stmt = sa.insert(
            db_models.EXIF
        ).values(
            item_uuid=item_uuid,
            exif=exif,
        )

        try:
            await self.db.execute(stmt)
        except asyncpg_exceptions.UniqueViolationError as exc:
            msg = 'EXIF data for item {item_uuid} already exists'
            raise exceptions.AlreadyExistsError(
                msg,
                item_uuid=item_uuid,
            ) from exc

    async def read_exif(self, item_uuid: UUID) -> dict[str, str]:
        """Return EXIF."""
        stmt = sa.select(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == item_uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'EXIF data for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

        return dict(response['exif'])

    async def update_exif(self, item_uuid: UUID, exif: dict[str, str]) -> None:
        """Update EXIF."""
        insert = pg_insert(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == item_uuid
        ).values(
            exif=exif,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.EXIF.item_uuid],
            set_={
                'tags': insert.excluded.tags,
            }
        )

        await self.db.execute(stmt)

    async def delete_exif(self, item_uuid: UUID) -> None:
        """Delete EXIF."""
        stmt = sa.delete(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == item_uuid
        ).returning(1)

        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'EXIF data for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)
