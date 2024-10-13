"""Repository that performs various operations on different objects."""

from collections.abc import Collection
from datetime import datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import models
from omoide import utils
from omoide.storage import interfaces
from omoide.storage.database import db_models
from omoide.storage.implementations import asyncpg


class MiscRepo(interfaces.AbsMiscRepo, asyncpg.AsyncpgStorage):
    """Repository that performs various operations on different objects."""

    async def get_computed_tags(self, item: models.Item) -> set[str]:
        """Get computed tags for this item."""
        stmt = sa.select(db_models.ComputedTags.tags).where(
            db_models.ComputedTags.item_uuid == item.uuid
        )
        response = await self.db.fetch_all(stmt)
        return {str(row) for row in response}

    async def update_computed_tags(
        self,
        item: models.Item,
        parent_computed_tags: set[str],
    ) -> set[str]:
        """Update computed tags for this item."""
        computed_tags = item.get_computed_tags(parent_computed_tags)

        insert = pg_insert(db_models.ComputedTags).values(
            item_uuid=item.uuid,
            tags=tuple(computed_tags),
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.ComputedTags.item_uuid],
            set_={'tags': insert.excluded.tags},
        )

        await self.db.execute(stmt)
        return computed_tags

    async def update_known_tags(
        self,
        users: Collection[models.User],
        tags_added: Collection[str],
        tags_deleted: Collection[str],
    ) -> None:
        """Update counters for known tags."""
        for user in users:
            if user.is_anon:
                await self.incr_known_tags_anon(tags_added)
                await self.decr_known_tags_anon(tags_deleted)
            else:
                await self.incr_known_tags_known(user, tags_added)
                await self.decr_known_tags_known(user, tags_deleted)

    async def incr_known_tags_anon(
        self,
        tags: Collection[str],
    ) -> None:
        """Increment tag counter."""
        for tag in tags:
            insert = pg_insert(db_models.KnownTagsAnon).values(
                tag=tag.casefold(),
                counter=1,
            )

            stmt = insert.on_conflict_do_update(
                index_elements=[
                    db_models.KnownTagsAnon.tag,
                ],
                set_={'counter': insert.excluded.counter + 1},
            )

            await self.db.execute(stmt)

    async def decr_known_tags_anon(
        self,
        tags: Collection[str],
    ) -> None:
        """Decrement tag counter."""
        for tag in tags:
            stmt = (
                sa.update(db_models.KnownTagsAnon)
                .where(
                    db_models.KnownTagsAnon.tag == tag.casefold(),
                )
                .values(
                    counter=db_models.KnownTagsAnon.counter - 1,
                )
            )

            await self.db.execute(stmt)

    async def incr_known_tags_known(
        self,
        user: models.User,
        tags: Collection[str],
    ) -> None:
        """Increment tag counter."""
        for tag in tags:
            insert = pg_insert(db_models.KnownTags).values(
                user_uuid=user.uuid,
                tag=tag.casefold(),
                counter=1,
            )

            stmt = insert.on_conflict_do_update(
                index_elements=[
                    db_models.KnownTags.user_uuid,
                    db_models.KnownTags.tag,
                ],
                set_={'counter': insert.excluded.counter + 1},
            )

            await self.db.execute(stmt)

    async def decr_known_tags_known(
        self,
        user: models.User,
        tags: Collection[str],
    ) -> None:
        """Decrement tag counter."""
        for tag in tags:
            stmt = (
                sa.update(db_models.KnownTags)
                .where(
                    db_models.KnownTags.user_uuid == user.uuid,
                    db_models.KnownTags.tag == tag.casefold(),
                )
                .values(
                    counter=db_models.KnownTags.counter - 1,
                )
            )

            await self.db.execute(stmt)

    async def drop_unused_known_tags_anon(self) -> None:
        """Drop tags with counter less of equal to 0."""
        stmt = sa.delete(db_models.KnownTagsAnon).where(
            db_models.KnownTagsAnon.counter <= 0,
        )
        await self.db.execute(stmt)

    async def drop_unused_known_tags_known(self, user: models.User) -> None:
        """Drop tags with counter less of equal to 0."""
        stmt = sa.delete(db_models.KnownTags).where(
            db_models.KnownTags.user_uuid == user.uuid,
            db_models.KnownTags.counter <= 0,
        )
        await self.db.execute(stmt)

    async def save_md5_signature(
        self,
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

        await self.db.execute(stmt)

    async def save_cr32_signature(
        self,
        item: models.Item,
        signature: str,
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

        await self.db.execute(stmt)

    async def start_long_job(
        self,
        name: str,
        user_uuid: UUID,
        target_uuid: UUID | None,
        added: Collection[str],
        deleted: Collection[str],
        started: datetime,
        extras: dict[str, Any],
    ) -> int:
        """Start long job."""
        stmt = (
            sa.insert(db_models.LongJob)
            .values(
                name=name,
                user_uuid=user_uuid,
                target_uuid=target_uuid,
                added=list(added),
                deleted=list(deleted),
                status='started',
                started=started,
                duration=None,
                operations=None,
                extras=extras,
                error='',
            )
            .returning(db_models.LongJob.id)
        )

        return int(await self.db.execute(stmt))

    async def finish_long_job(
        self,
        id: int,
        status: str,
        duration: float,
        operations: int,
        error: str,
    ) -> None:
        """Finish long job."""
        stmt = (
            sa.update(db_models.LongJob)
            .values(
                status=status,
                duration=duration,
                operations=operations,
                error=error,
            )
            .where(db_models.LongJob.id == id)
        )

        await self.db.execute(stmt)

    async def create_serial_operation(
        self,
        name: str,
        extras: dict[str, Any] | None = None,
    ) -> int:
        """Create serial operation."""
        now = utils.now()

        stmt = (
            sa.insert(db_models.SerialOperation)
            .values(
                name=name,
                worker_name=None,
                status='created',
                extras=extras or {},
                created_at=now,
                updated_at=now,
                started_at=None,
                ended_at=None,
                log=None,
            )
            .returning(db_models.SerialOperation.id)
        )

        return int(await self.db.execute(stmt))
