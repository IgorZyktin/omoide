"""Repository that performs various operations on different objects."""
import abc
from collections import defaultdict
from collections.abc import Collection
from datetime import datetime
from typing import Any
from typing import Awaitable
from typing import Callable
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import domain  # FIXME - use models instead
from omoide import models
from omoide.storage import interfaces
from omoide.storage.database import db_models
from omoide.storage.implementations import asyncpg
from omoide.storage.implementations.asyncpg.repositories import queries


class _MiscRepoBase(interfaces.AbsMiscRepo, asyncpg.AsyncpgStorage, abc.ABC):
    """Helper methods here."""

    @staticmethod
    def _convert_known_tags_to_rows(
        user_uuid: UUID | None,
        known_tags: dict[str, int],
    ) -> list[dict[str, str | int]]:
        """Convert from {'cat': 1} to [{'tag': 'cat', 'counter': 1}]."""
        if user_uuid is None:
            return [
                {'tag': tag, 'counter': counter}
                for tag, counter in known_tags.items()
            ]

        user_uuid_str = str(user_uuid)
        return [
            {'user_uuid': user_uuid_str, 'tag': tag, 'counter': counter}
            for tag, counter in known_tags.items()
        ]

    async def _get_available_tags_anon(
        self,
        marker: UUID | None,
        limit: int,
    ) -> list[tuple[str, list[str]]]:
        """Return tags for available items."""
        sub_query = sa.select(db_models.PublicUsers.user_uuid)

        stmt = sa.select(
            db_models.Item.uuid,
            db_models.Item.tags,
        ).where(
            db_models.Item.owner_uuid.in_(sub_query),  # noqa
        )

        if marker is not None:
            stmt = stmt.where(db_models.Item.uuid > marker)

        stmt = stmt.order_by(db_models.Item.uuid).limit(limit)

        response = await self.db.fetch_all(stmt)

        return [(row['uuid'], row['tags']) for row in response]

    async def _get_available_tags_known(
        self,
        marker: UUID | None,
        limit: int,
        user_uuid: UUID,
    ) -> list[tuple[str, list[str]]]:
        """Return tags for available items."""
        stmt = sa.select(
            db_models.Item.uuid,
            db_models.Item.tags,
        ).where(
            sa.or_(
                db_models.Item.owner_uuid == user_uuid,
                db_models.Item.permissions.any(str(user_uuid)),
            )
        )

        if marker is not None:
            stmt = stmt.where(db_models.Item.uuid > marker)

        stmt = stmt.order_by(db_models.Item.uuid).limit(limit)

        response = await self.db.fetch_all(stmt)

        return [(row['uuid'], row['tags']) for row in response]

    @staticmethod
    async def _process_tags_batched(
        func: Callable[..., Awaitable[list[tuple[str, list[str]]]]],
        batch_size: int,
        *args: Any,
    ) -> dict[str, int]:
        """Recalculate all known tags for known user."""
        marker = None
        known_tags: dict[str, int] = defaultdict(int)

        while True:
            batch = await func(marker, batch_size, *args)

            for item_uuid, tags in batch:
                for tag in tags:
                    known_tags[tag.casefold()] += 1

                marker = item_uuid

            if len(batch) < batch_size or marker is None:
                break

        return dict(known_tags)


class MiscRepo(_MiscRepoBase):
    """Repository that performs various operations on different objects."""

    async def read_children_to_download(
        self,
        user: models.User,
        item: domain.Item,
    ) -> list[dict[str, UUID | str | int]]:
        """Return some components of the given item children with metainfo."""
        stmt = sa.select(
            db_models.Item.uuid,
            db_models.Metainfo.content_size,
            db_models.Item.content_ext,
        ).join(
            db_models.Metainfo,
            db_models.Metainfo.item_uuid == db_models.Item.uuid,
            isouter=True,
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        stmt = stmt.where(
            db_models.Item.parent_uuid == item.uuid,
            db_models.Item.is_collection == False,  # noqa
            db_models.Item.content_ext != None,  # noqa
            db_models.Metainfo.content_size != None,  # noqa
        ).order_by(
            db_models.Item.number,
        )

        response = await self.db.fetch_all(stmt)
        return [dict(x) for x in response]  # type: ignore

    @staticmethod
    def gather_tags(
        parent_uuid: UUID | None,
        parent_tags: list[str],
        item_uuid: UUID,
        item_tags: list[str],
    ) -> tuple[str, ...]:
        """Combine parent tags with item tags."""
        all_tags = {
            *(x.lower() for x in item_tags),
            str(item_uuid),
        }

        if parent_uuid is not None:
            clean_parent_uuid = str(parent_uuid).lower()
            clean_tags = (
                lower
                for x in parent_tags
                if (lower := x.lower()) != clean_parent_uuid
            )
            all_tags.update(clean_tags)

        return tuple(all_tags)

    async def update_computed_tags(self, item: models.Item) -> None:
        """Update computed tags for this item."""
        parent_tags: set[str] = set()

        if item.parent_uuid is not None:
            parent_tags_stmt = sa.select(
                db_models.ComputedTags.tags
            ).where(
                db_models.ComputedTags.item_uuid == item.parent_uuid
            )
            parent_tags_response = await self.db.execute(parent_tags_stmt)

            if parent_tags_response:
                parent_tags = set(parent_tags_response)

        computed_tags = item.get_computed_tags(parent_tags)

        insert = pg_insert(
            db_models.ComputedTags
        ).values(
            item_uuid=item.uuid,
            tags=tuple(computed_tags),
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.ComputedTags.item_uuid],
            set_={'tags': insert.excluded.tags}
        )

        await self.db.execute(stmt)

    async def replace_computed_tags(
        self,
        item: models.Item,
        tags: set[str]
    ) -> None:
        """Replace all computed tags for this item."""
        stmt = sa.update(
            db_models.ComputedTags
        ).where(
            db_models.ComputedTags.item_uuid == item.uuid
        ).values(
            tags=tuple(tags)
        )
        await self.db.execute(stmt)

    async def update_known_tags(
        self,
        users: Collection[models.User],
        tags_added: Collection[str],
        tags_deleted: Collection[str],
    ) -> None:
        """Update counters for known tags."""
        for user in users:
            if user.is_anon:
                await self._increment_known_tags_for_anon_user(tags_added)
                await self._decrement_known_tags_for_anon_user(tags_deleted)
            else:
                await self._increment_known_tags_for_known_user(user,
                                                                tags_added)
                await self._decrement_known_tags_for_known_user(user,
                                                                tags_deleted)

    async def _increment_known_tags_for_anon_user(
        self,
        tags: Collection[str],
    ) -> None:
        """Increment tag counter."""
        for tag in tags:
            insert = pg_insert(
                db_models.KnownTagsAnon
            ).values(
                tag=tag.casefold(),
                counter=1,
            )

            stmt = insert.on_conflict_do_update(
                index_elements=[
                    db_models.KnownTagsAnon.tag,
                ],
                set_={'counter': insert.excluded.counter + 1}
            )

            await self.db.execute(stmt)

    async def _decrement_known_tags_for_anon_user(
        self,
        tags: Collection[str],
    ) -> None:
        """Decrement tag counter."""
        for tag in tags:
            stmt = sa.update(
                db_models.KnownTagsAnon
            ).where(
                db_models.KnownTagsAnon.tag == tag.casefold(),
            ).values(
                counter=db_models.KnownTagsAnon.counter - 1,
            )

            await self.db.execute(stmt)

    async def _increment_known_tags_for_known_user(
        self,
        user: models.User,
        tags: Collection[str],
    ) -> None:
        """Increment tag counter."""
        for tag in tags:
            insert = pg_insert(
                db_models.KnownTags
            ).values(
                user_uuid=user.uuid,
                tag=tag.casefold(),
                counter=1,
            )

            stmt = insert.on_conflict_do_update(
                index_elements=[
                    db_models.KnownTags.user_uuid,
                    db_models.KnownTags.tag,
                ],
                set_={'counter': insert.excluded.counter + 1}
            )

            await self.db.execute(stmt)

    async def _decrement_known_tags_for_known_user(
        self,
        user: models.User,
        tags: Collection[str],
    ) -> None:
        """Decrement tag counter."""
        for tag in tags:
            stmt = sa.update(
                db_models.KnownTags
            ).where(
                db_models.KnownTags.user_uuid == user.uuid,
                db_models.KnownTags.tag == tag.casefold(),
            ).values(
                counter=db_models.KnownTags.counter - 1,
            )

            await self.db.execute(stmt)

    async def drop_unused_known_tags(
        self,
        users: Collection[models.User],
        public_users: set[UUID],
    ) -> None:
        """Drop tags with counter less of equal to 0."""
        for user in users:
            if user.is_not_anon:
                stmt = sa.delete(
                    db_models.KnownTags
                ).where(
                    db_models.KnownTags.user_uuid == user.uuid,
                    db_models.KnownTags.counter <= 0,
                )
                await self.db.execute(stmt)

            elif user.is_anon or user.uuid in public_users:
                stmt = sa.delete(
                    db_models.KnownTagsAnon
                ).where(
                    db_models.KnownTagsAnon.counter <= 0,
                )
                await self.db.execute(stmt)

    async def calculate_known_tags_anon(
        self,
        batch_size: int,
    ) -> dict[str, int]:
        """Recalculate all known tags for anon."""
        return await self._process_tags_batched(
            self._get_available_tags_anon, batch_size)

    async def calculate_known_tags_known(
        self,
        user: models.User,
        batch_size: int,
    ) -> dict[str, int]:
        """Recalculate all known tags for known user."""
        return await self._process_tags_batched(
            self._get_available_tags_known, batch_size, user.uuid)

    async def insert_known_tags_anon(
        self,
        known_tags: dict[str, int],
    ) -> None:
        """Insert batch of known tags."""
        tag_rows = self._convert_known_tags_to_rows(None, known_tags)
        stmt = sa.insert(db_models.KnownTagsAnon)
        await self.db.execute_many(stmt, tag_rows)

    async def insert_known_tags_known(
        self,
        user: models.User,
        known_tags: dict[str, int],
    ) -> None:
        """Insert batch of known tags."""
        tag_rows = self._convert_known_tags_to_rows(user.uuid, known_tags)
        stmt = sa.insert(db_models.KnownTags)
        await self.db.execute_many(stmt, tag_rows)

    async def drop_known_tags_anon(self) -> None:
        """Clean all known tags for anon."""
        stmt = sa.delete(db_models.KnownTagsAnon)
        await self.db.execute(stmt)

    async def drop_known_tags_known(self, user: models.User) -> None:
        """Clean all known tags for known user."""
        stmt = sa.delete(
            db_models.KnownTags
        ).where(
            db_models.KnownTags.user_uuid == user.uuid
        )
        await self.db.execute(stmt)

    async def save_md5_signature(
        self,
        item: models.Item,
        signature: str
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

    async def save_cr32_signature(
        self,
        item: models.Item,
        signature: str
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
        stmt = sa.insert(
            db_models.LongJob
        ).values(
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
        ).returning(
            db_models.LongJob.id
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
        stmt = sa.update(
            db_models.LongJob
        ).values(
            status=status,
            duration=duration,
            operations=operations,
            error=error,
        ).where(
            db_models.LongJob.id == id
        )

        await self.db.execute(stmt)
