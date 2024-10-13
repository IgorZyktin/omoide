"""Repository that perform CRUD operations on metainfo."""

from typing import Any
from uuid import UUID

import sqlalchemy as sa

from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.storage import interfaces as storage_interfaces
from omoide.storage.database import db_models
from omoide.storage.implementations import asyncpg


class MetainfoRepo(storage_interfaces.AbsMetainfoRepo, asyncpg.AsyncpgStorage):
    """Repository that perform CRUD operations on metainfo."""

    async def create_metainfo(self, metainfo: models.Metainfo) -> None:
        """Create metainfo."""
        stmt = sa.insert(db_models.Metainfo).values(**metainfo.model_dump())
        await self.db.execute(stmt)

    async def read_metainfo(self, item: models.Item) -> models.Metainfo:
        """Return metainfo."""
        stmt = sa.select(db_models.Metainfo).where(
            db_models.Metainfo.item_uuid == item.uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item.uuid)

        return models.Metainfo(**response)

    async def get_metainfos(
        self,
        items: list[models.Item],
    ) -> dict[UUID, models.Metainfo | None]:  # TODO use item_id, not UUID
        """Return many metainfo records."""
        uuids = [item.uuid for item in items]
        metainfos: dict[UUID, models.Metainfo | None] = dict.fromkeys(uuids)

        query = sa.select(db_models.Metainfo).where(
            db_models.Metainfo.item_uuid.in_(  # noqa
                tuple(str(uuid) for uuid in uuids)
            )
        )

        response = await self.db.fetch_all(query)
        for row in response:
            model = models.Metainfo(**row)
            metainfos[model.item_uuid] = model

        return metainfos

    async def update_metainfo(
        self,
        user: models.User,
        item_uuid: UUID,
        metainfo: models.Metainfo,
    ) -> None:
        """Update metainfo."""
        stmt = (
            sa.update(db_models.Metainfo)
            .where(db_models.Metainfo.item_uuid == item_uuid)
            .values(**metainfo.model_dump(exclude={'item_uuid', 'created_at'}))
            .returning(1)
        )

        response = await self.db.execute(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

    async def mark_metainfo_updated(self, item_uuid: UUID) -> None:
        """Set last updated to current datetime."""
        stmt = (
            sa.update(db_models.Metainfo)
            .values(updated_at=utils.now())
            .where(db_models.Metainfo.item_uuid == item_uuid)
            .returning(1)
        )

        response = await self.db.execute(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

    async def update_metainfo_extras(
        self,
        item_uuid: UUID,
        new_extras: dict[str, Any],
    ) -> None:
        """Add new data to extras."""
        if not new_extras:
            return

        for key, value in new_extras.items():
            stmt = (
                sa.update(db_models.Metainfo)
                .where(db_models.Metainfo.item_uuid == item_uuid)
                .values(
                    extras=sa.func.jsonb_set(
                        db_models.Metainfo.extras,
                        [key],
                        f'"{value}"' if isinstance(value, str) else value,
                    )
                )
            )
            await self.db.execute(stmt)

        await self.mark_metainfo_updated(item_uuid)

    async def get_total_disk_usage(
        self,
        user: models.User,
    ) -> models.DiskUsage:
        """Return total disk usage for specified user."""
        stmt = (
            sa.select(
                sa.func.sum(
                    sa.func.coalesce(db_models.Metainfo.content_size, 0)
                ).label('content_bytes'),
                sa.func.sum(
                    sa.func.coalesce(db_models.Metainfo.preview_size, 0)
                ).label('preview_bytes'),
                sa.func.sum(
                    sa.func.coalesce(db_models.Metainfo.thumbnail_size, 0)
                ).label('thumbnail_bytes'),
            )
            .join(
                db_models.Item,
                db_models.Item.uuid == db_models.Metainfo.item_uuid,
            )
            .where(db_models.Item.owner_uuid == user.uuid)
        )

        response = await self.db.fetch_one(stmt)

        return models.DiskUsage(**response)
