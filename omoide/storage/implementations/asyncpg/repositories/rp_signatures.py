"""Repository that performs various operations on different objects."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import models
from omoide.storage import interfaces
from omoide.storage.database import db_models
from omoide.storage.implementations import asyncpg


class SignaturesRepo(interfaces.AbsSignaturesRepo, asyncpg.AsyncpgStorage):
    """Repository that performs various operations on different objects."""

    async def get_md5_signature(self, item: models.Item) -> str | None:
        """Get signature record."""
        query = sa.select(
            db_models.SignatureMD5.signature
        ).where(
            db_models.SignatureMD5.item_id == item.id
        )

        response = await self.db.fetch_one(query)

        if response is None:
            return None

        return response

    async def get_md5_signatures(
        self,
        items: list[models.Item],
    ) -> dict[int, str | None]:
        """Get many signatures."""
        ids = [item.id for item in items]
        signatures: dict[int, str | None] = dict.fromkeys(ids)

        query = sa.select(
            db_models.SignatureCRC32.item_id,
            db_models.SignatureCRC32.signature,
        ).where(
            db_models.SignatureCRC32.item_id.in_(tuple(ids))  # noqa
        )

        response = await self.db.fetch_all(query)
        for row in response:
            signatures[row['item_id']] = row['signature']

        return signatures

    async def save_md5_signature(
        self,
        item: models.Item,
        signature: str,
    ) -> None:
        """Create signature record."""
        insert = pg_insert(
            db_models.SignatureMD5
        ).values(
            item_id=item.id,
            signature=signature,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.SignatureMD5.item_id],
            set_={'signature': insert.excluded.signature}
        )

        await self.db.execute(stmt)

    async def get_cr32_signature(self, item: models.Item) -> int | None:
        """Get signature record."""
        query = sa.select(
            db_models.SignatureCRC32.signature
        ).where(
            db_models.SignatureCRC32.item_id == item.id
        )

        response = await self.db.fetch_one(query)

        if response is None:
            return None

        return response

    async def get_cr32_signatures(
        self,
        items: list[models.Item],
    ) -> dict[int, int | None]:
        """Get many signatures."""
        ids = [item.id for item in items]
        signatures: dict[int, str | None] = dict.fromkeys(ids)

        query = sa.select(
            db_models.SignatureCRC32.item_id,
            db_models.SignatureCRC32.signature,
        ).where(
            db_models.SignatureCRC32.item_id.in_(tuple(ids))  # noqa
        )

        response = await self.db.fetch_all(query)
        for row in response:
            signatures[row['item_id']] = row['signature']

        return signatures

    async def save_cr32_signature(
        self,
        item: models.Item,
        signature: str,
    ) -> None:
        """Create signature record."""
        insert = pg_insert(
            db_models.SignatureCRC32
        ).values(
            item_id=item.id,
            signature=signature,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.SignatureCRC32.item_id],
            set_={'signature': insert.excluded.signature}
        )

        await self.db.execute(stmt)
