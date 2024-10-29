"""Repository that performs various operations related to image signatures."""

from collections.abc import Collection

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_signatures_repo import AbsSignaturesRepo


class SignaturesRepo(AbsSignaturesRepo[AsyncConnection]):
    """Repository that performs various operations related to image signatures."""

    async def get_md5_signature(
        self,
        conn: AsyncConnection,
        item: models.Item,
    ) -> str | None:
        """Get signature record."""
        query = sa.select(db_models.SignatureMD5.signature).where(
            db_models.SignatureMD5.item_id == item.id
        )
        return (await conn.execute(query)).scalar()

    async def get_md5_signatures_map(
        self,
        conn: AsyncConnection,
        items: Collection[models.Item],
    ) -> dict[int, str | None]:
        """Get map of MD5 signatures."""
        ids = [item.id for item in items]
        signatures: dict[int, str | None] = dict.fromkeys(ids)

        query = sa.select(
            db_models.SignatureMD5.item_id,
            db_models.SignatureMD5.signature,
        ).where(db_models.SignatureMD5.item_id.in_(ids))

        response = (await conn.execute(query)).fetchall()
        for row in response:
            signatures[row.item_id] = row.signature

        return signatures

    async def save_md5_signature(
        self,
        conn: AsyncConnection,
        item: models.Item,
        signature: str,
    ) -> None:
        """Create signature record."""
        insert = pg_insert(db_models.SignatureMD5).values(
            item_id=item.id,
            signature=signature,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.SignatureMD5.item_id],
            set_={'signature': insert.excluded.signature},
        )

        await conn.execute(stmt)

    async def get_cr32_signature(
        self,
        conn: AsyncConnection,
        item: models.Item,
    ) -> int | None:
        """Get signature record."""
        query = sa.select(db_models.SignatureCRC32.signature).where(
            db_models.SignatureCRC32.item_id == item.id
        )
        return (await conn.execute(query)).scalar()

    async def get_cr32_signatures_map(
        self,
        conn: AsyncConnection,
        items: Collection[models.Item],
    ) -> dict[int, int | None]:
        """Get map of CRC32 signatures."""
        ids = [item.id for item in items]
        signatures: dict[int, int | None] = dict.fromkeys(ids)

        query = sa.select(
            db_models.SignatureCRC32.item_id,
            db_models.SignatureCRC32.signature,
        ).where(db_models.SignatureCRC32.item_id.in_(ids))

        response = (await conn.execute(query)).fetchall()
        for row in response:
            signatures[row.item_id] = row.signature

        return signatures

    async def save_cr32_signature(
        self,
        conn: AsyncConnection,
        item: models.Item,
        signature: int,
    ) -> None:
        """Create signature record."""
        insert = pg_insert(db_models.SignatureCRC32).values(
            item_id=item.id,
            signature=signature,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.SignatureCRC32.item_id],
            set_={'signature': insert.excluded.signature},
        )

        await conn.execute(stmt)
