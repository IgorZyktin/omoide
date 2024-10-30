"""Repository that performs operations on tags."""

import abc
from collections import defaultdict
from collections.abc import Callable
import itertools

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_tags_repo import AbsTagsRepo


class _TagsRepoHelper(AbsTagsRepo[AsyncConnection], abc.ABC):
    """Helper class."""

    @staticmethod
    async def _process_batch_of_tags(
        conn: AsyncConnection,
        get_conditions: Callable[[int], list[sa.ColumnElement]],
        batch_size: int,
    ) -> dict[str, int]:
        """Process batch of tags load."""
        known_tags: dict[str, int] = defaultdict(int)
        marker = -1

        while True:
            stmt = (
                (
                    sa.select(
                        db_models.Item.id,
                        db_models.ComputedTags.tags,
                    )
                    .join(
                        db_models.ComputedTags,
                        db_models.ComputedTags.item_uuid == db_models.Item.uuid,
                    )
                    .where(*get_conditions(marker))
                )
                .order_by(db_models.Item.id)
                .limit(batch_size)
            )

            response = (await conn.execute(stmt)).fetchall()

            for item_id, item_tags in response:
                for item_tag in item_tags:
                    known_tags[item_tag.casefold()] += 1
                marker = item_id

            if len(response) < batch_size:
                break

        return dict(known_tags)


class TagsRepo(_TagsRepoHelper):
    """Repository that performs operations on tags."""

    async def get_known_tags_anon(
        self,
        conn: AsyncConnection,
        batch_size: int,
    ) -> dict[str, int]:
        """Return known tags for anon."""
        public_users = sa.select(db_models.PublicUsers.user_uuid)

        def get_conditions(_marker: int) -> list[sa.ColumnElement]:
            """Return list of filtering conditions."""
            return [
                db_models.Item.owner_uuid.in_(public_users),
                db_models.Item.id > _marker,
            ]

        return await self._process_batch_of_tags(
            conn=conn,
            get_conditions=get_conditions,
            batch_size=batch_size,
        )

    async def drop_known_tags_anon(self, conn: AsyncConnection) -> int:
        """Drop all known tags for anon user."""
        stmt = sa.delete(db_models.KnownTagsAnon)
        response = await conn.execute(stmt)
        return int(response.rowcount)

    async def insert_known_tags_anon(
        self,
        conn: AsyncConnection,
        tags: dict[str, int],
        batch_size: int,
    ) -> None:
        """Insert given tags for anon user."""
        payload = [{'tag': str(tag), 'counter': counter} for tag, counter in tags.items()]

        for batch in itertools.batched(payload, batch_size):
            stmt = sa.insert(db_models.KnownTagsAnon).values(batch)
            await conn.execute(stmt)

    async def get_known_tags_user(
        self,
        conn: AsyncConnection,
        user: models.User,
        batch_size: int,
    ) -> dict[str, int]:
        """Return known tags for specific user."""

        def get_conditions(_marker: int) -> list[sa.ColumnElement]:
            """Return list of filtering conditions."""
            return [
                sa.or_(
                    db_models.Item.owner_uuid == user.uuid,
                    db_models.Item.permissions.any(str(user.uuid)),
                ),
                db_models.Item.id > _marker,
            ]

        return await self._process_batch_of_tags(
            conn=conn,
            get_conditions=get_conditions,
            batch_size=batch_size,
        )

    async def drop_known_tags_user(
        self,
        conn: AsyncConnection,
        user: models.User,
    ) -> int:
        """Drop all known tags for specific user."""
        stmt = sa.delete(db_models.KnownTags).where(db_models.KnownTags.user_id == user.id)
        response = await conn.execute(stmt)
        return int(response.rowcount)

    async def insert_known_tags_user(
        self,
        conn: AsyncConnection,
        user: models.User,
        tags: dict[str, int],
        batch_size: int,
    ) -> None:
        """Insert given tags for specific user."""
        payload = [
            {'user_id': user.id, 'tag': str(tag), 'counter': counter}
            for tag, counter in tags.items()
        ]

        for batch in itertools.batched(payload, batch_size):
            stmt = sa.insert(db_models.KnownTags).values(batch)
            await conn.execute(stmt)

    async def get_computed_tags(
        self,
        conn: AsyncConnection,
        item: models.Item,
    ) -> set[str]:
        """Return computed tags for given item."""
        stmt = sa.select(db_models.ComputedTags.tags).where(
            db_models.ComputedTags.item_uuid == item.uuid
        )
        response = (await conn.execute(stmt)).scalar()
        return set(response.tags)

    async def save_computed_tags(
        self,
        conn: AsyncConnection,
        item: models.Item,
        tags: set[str],
    ) -> None:
        """Save computed tags for given item."""
        insert = pg_insert(db_models.ComputedTags).values(
            item_uuid=item.uuid,
            tags=tuple(tags),
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.ComputedTags.item_uuid],
            set_={'tags': insert.excluded.tags},
        )

        await conn.execute(stmt)
