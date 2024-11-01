"""Repository that perform CRUD operations on metainfo."""

from collections.abc import Collection

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.database import db_models
from omoide.database.interfaces.abs_meta_repo import AbsMetaRepo


class MetaRepo(AbsMetaRepo[AsyncConnection]):
    """Repository that perform CRUD operations on metainfo."""

    async def create(self, conn: AsyncConnection, metainfo: models.Metainfo) -> None:
        """Create metainfo."""
        stmt = sa.insert(db_models.Metainfo).values(**metainfo.model_dump())
        await conn.execute(stmt)

    async def get_by_item(self, conn: AsyncConnection, item: models.Item) -> models.Metainfo:
        """Return metainfo."""
        query = sa.select(db_models.Metainfo).where(db_models.Metainfo.item_id == item.id)

        response = (await conn.execute(query)).fetchone()

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item.uuid)

        return db_models.Metainfo.cast(response)

    async def get_metainfo_map(
        self,
        conn: AsyncConnection,
        items: Collection[models.Item],
    ) -> dict[int, models.Metainfo | None]:
        """Return many metainfo records."""
        ids = [item.id for item in items]
        metainfos: dict[int, models.Metainfo | None] = dict.fromkeys(ids)

        query = sa.select(db_models.Metainfo).where(db_models.Metainfo.item_id.in_(ids))

        response = (await conn.execute(query)).fetchall()

        for row in response:
            model = db_models.Metainfo.cast(row)
            metainfos[model.item_id] = model

        return metainfos

    async def save(self, conn: AsyncConnection, metainfo: models.Metainfo) -> None:
        """Update metainfo."""
        stmt = (
            sa.update(db_models.Metainfo)
            .where(db_models.Metainfo.item_id == metainfo.item_id)
            .values(**metainfo.get_changes())
            .returning(1)
        )

        response = await conn.execute(stmt)

        if response is None:
            msg = 'Metainfo for item {item_id} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=metainfo.item_id)

    async def soft_delete(self, conn: AsyncConnection, metainfo: models.Metainfo) -> int:
        """Mark item deleted."""
        stmt = (
            sa.update(db_models.Metainfo)
            .where(db_models.Metainfo.item_id == metainfo.item_id)
            .values(
                updated_at=utils.now(),
                deleted_at=utils.now(),
            )
        )

        response = await conn.execute(stmt)
        return int(response.rowcount)

    async def add_item_note(
        self,
        conn: AsyncConnection,
        item: models.Item,
        key: str,
        value: str,
    ) -> None:
        """Add new note to given item."""
        insert = pg_insert(db_models.ItemNote).values(
            item_id=item.id,
            key=key,
            value=value,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[
                db_models.ItemNote.item_id,
                db_models.ItemNote.key,
            ],
            set_={'value': insert.excluded.value},
        )

        await conn.execute(stmt)

    async def get_item_notes(self, conn: AsyncConnection, item: models.Item) -> dict[str, str]:
        """Return notes for given item."""
        query = sa.select(
            sa.func.json_object_agg(db_models.ItemNote.key, db_models.ItemNote.value)
        ).where(db_models.ItemNote.item_id == item.id)
        response = (await conn.execute(query)).scalar()
        return response or {}

    async def get_total_disk_usage(
        self,
        conn: AsyncConnection,
        user: models.User,
    ) -> models.DiskUsage:
        """Return total disk usage for specified user."""
        query = (
            sa.select(
                sa.func.sum(sa.func.coalesce(db_models.Metainfo.content_size, 0)).label(
                    'content_bytes'
                ),
                sa.func.sum(sa.func.coalesce(db_models.Metainfo.preview_size, 0)).label(
                    'preview_bytes'
                ),
                sa.func.sum(sa.func.coalesce(db_models.Metainfo.thumbnail_size, 0)).label(
                    'thumbnail_bytes'
                ),
            )
            .join(
                db_models.Item,
                db_models.Item.id == db_models.Metainfo.item_id,
            )
            .where(db_models.Item.owner_id == user.id)
        )

        response = (await conn.execute(query)).fetchone()

        return models.DiskUsage(
            content_bytes=response.content_bytes if response else 0,
            preview_bytes=response.preview_bytes if response else 0,
            thumbnail_bytes=response.thumbnail_bytes if response else 0,
        )
