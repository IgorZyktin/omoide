"""Repository that performs CRUD operations on EXIF."""

from typing import Any

from asyncpg import exceptions as asyncpg_exceptions
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import exceptions
from omoide import models
from omoide.storage import interfaces
from omoide.database import db_models
from omoide.storage.implementations import asyncpg


class EXIFRepository(interfaces.AbsEXIFRepository, asyncpg.AsyncpgStorage):
    """Repository that performs CRUD operations on EXIF."""

    async def create_exif(
        self,
        item: models.Item,
        exif: dict[str, Any],
    ) -> None:
        """Create EXIF for given item."""
        stmt = sa.insert(db_models.EXIF).values(item_id=item.id, exif=exif)

        try:
            await self.db.execute(stmt)
        except asyncpg_exceptions.UniqueViolationError as exc:
            msg = 'EXIF data for item {item_uuid} already exists'
            raise exceptions.AlreadyExistsError(
                msg,
                item_uuid=item.uuid,
            ) from exc

    async def read_exif(self, item: models.Item) -> dict[str, Any]:
        """Return EXIF for given item."""
        stmt = sa.select(db_models.EXIF).where(
            db_models.EXIF.item_id == item.id
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'EXIF data for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item.uuid)

        return dict(response['exif'])

    async def update_exif(
        self,
        item: models.Item,
        exif: dict[str, Any],
    ) -> None:
        """Update EXIF for given item."""
        insert = (
            pg_insert(db_models.EXIF)
            .where(db_models.EXIF.item_id == item.id)
            .values(exif=exif)
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.EXIF.item_id],
            set_={'exif': insert.excluded.exif},
        )

        await self.db.execute(stmt)

    async def delete_exif(self, item: models.Item) -> None:
        """Delete EXIF for given item."""
        stmt = (
            sa.delete(db_models.EXIF)
            .where(db_models.EXIF.item_id == item.id)
            .returning(1)
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'EXIF data for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item.uuid)
