"""Repository that perform CRUD operations on metainfo."""
from uuid import UUID

import sqlalchemy as sa

from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.storage.asyncpg_storage import AsyncpgStorage
from omoide.storage.database import db_models
from omoide.storage import interfaces


class MetainfoRepo(interfaces.AbsMetainfoRepo, AsyncpgStorage):
    """Repository that perform CRUD operations on metainfo."""

    async def create_empty_metainfo(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> None:
        """Create metainfo with blank fields."""
        stmt = sa.insert(
            db_models.Metainfo
        ).values(
            item_uuid=item_uuid,
            created_at=utils.now(),
            updated_at=utils.now(),
            extras={},
        )

        await self.db.execute(stmt)

    async def read_metainfo(self, item_uuid: UUID) -> models.Metainfo:
        """Return metainfo."""
        stmt = sa.select(
            db_models.Metainfo
        ).where(
            db_models.Metainfo.item_uuid == item_uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

        return models.Metainfo(**response)

    async def update_metainfo(
        self,
        user: models.User,
        item_uuid: UUID,
        metainfo: models.Metainfo,
    ) -> None:
        """Update metainfo."""
        stmt = sa.update(
            db_models.Metainfo
        ).where(
            db_models.Metainfo.item_uuid == item_uuid
        ).values(
            **metainfo.model_dump(exclude={'item_uuid', 'created_at'})
        ).returning(1)

        response = await self.db.execute(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

    async def mark_metainfo_updated(self, item_uuid: UUID) -> None:
        """Set last updated to current datetime."""
        stmt = sa.update(
            db_models.Metainfo
        ).values(
            updated_at=utils.now()
        ).where(
            db_models.Metainfo.item_uuid == item_uuid
        ).returning(1)

        response = await self.db.execute(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

    async def update_metainfo_extras(
        self,
        uuid: UUID,
        new_extras: dict[str, None | int | float | str | bool],
    ) -> None:
        """Add new data to extras."""
        for key, value in new_extras.items():
            stmt = sa.update(
                db_models.Metainfo
            ).where(
                db_models.Metainfo.item_uuid == uuid
            ).values(
                extras=sa.func.jsonb_set(
                    db_models.Metainfo.extras,
                    [key],
                    f'"{value}"' if isinstance(value, str) else value,
                )
            )
            await self.db.execute(stmt)
