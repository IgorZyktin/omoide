"""Repository that performs operations on tags."""

import itertools

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import models
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import queries
from omoide.database.interfaces.abs_tags_repo import AbsTagsRepo


class TagsRepo(AbsTagsRepo[AsyncConnection]):
    """Repository that performs operations on tags."""

    async def calculate_known_tags_anon(self, conn: AsyncConnection) -> dict[str, int]:
        """Return known tags for anon."""
        query_ids = sa.select(db_models.Item.id).where(
            db_models.Item.owner_id.in_(queries.public_user_ids())
        )

        query_tags = sa.select(sa.func.unnest(db_models.ComputedTags.tags).label('tag')).where(
            db_models.ComputedTags.item_id.in_(query_ids)
        )

        query = sa.select(query_tags.c.tag, sa.func.count().label('total')).group_by(
            query_tags.c.tag
        )

        response = (await conn.execute(query)).fetchall()
        return {row.tag: row.total for row in response}

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

    async def increment_known_tags_user(
        self,
        conn: AsyncConnection,
        user: models.User,
        tags: set[str],
    ) -> None:
        """Increase counter for given tags."""
        for tag in tags:
            stmt = (
                sa.update(db_models.KnownTags)
                .where(db_models.KnownTags.user_id == user.id, db_models.KnownTags.tag == tag)
                .values(counter=sa.func.greatest(0, db_models.KnownTags.counter) + 1)
            )
            await conn.execute(stmt)

    async def increment_known_tags_anon(self, conn: AsyncConnection, tags: set[str]) -> None:
        """Increase counter for given tags."""
        for tag in tags:
            stmt = (
                sa.update(db_models.KnownTagsAnon)
                .where(db_models.KnownTagsAnon.tag == tag)
                .values(counter=sa.func.greatest(0, db_models.KnownTagsAnon.counter) + 1)
            )
            await conn.execute(stmt)

    async def decrement_known_tags_user(
        self,
        conn: AsyncConnection,
        user: models.User,
        tags: set[str],
    ) -> None:
        """Decrease counter for given tags."""
        for tag in tags:
            stmt = (
                sa.update(db_models.KnownTags)
                .where(db_models.KnownTags.user_id == user.id, db_models.KnownTags.tag == tag)
                .values(counter=sa.func.greatest(0, db_models.KnownTags.counter - 1))
            )
            await conn.execute(stmt)

    async def decrement_known_tags_anon(self, conn: AsyncConnection, tags: set[str]) -> None:
        """Decrease counter for given tags."""
        for tag in tags:
            stmt = (
                sa.update(db_models.KnownTagsAnon)
                .where(db_models.KnownTagsAnon.tag == tag)
                .values(counter=sa.func.greatest(0, db_models.KnownTagsAnon.counter - 1))
            )
            await conn.execute(stmt)

    async def calculate_known_tags_user(
        self, conn: AsyncConnection, user: models.User
    ) -> dict[str, int]:
        """Return known tags for specific user."""
        query_ids = sa.select(db_models.Item.id).where(
            sa.or_(
                db_models.Item.owner_id == user.id,
                db_models.Item.permissions.any_() == user.id,
            )
        )

        query_tags = sa.select(sa.func.unnest(db_models.ComputedTags.tags).label('tag')).where(
            db_models.ComputedTags.item_id.in_(query_ids)
        )

        query = sa.select(query_tags.c.tag, sa.func.count().label('total')).group_by(
            query_tags.c.tag
        )

        response = (await conn.execute(query)).fetchall()
        return {row.tag: row.total for row in response}

    async def drop_known_tags_user(self, conn: AsyncConnection, user: models.User) -> int:
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

    async def get_computed_tags(self, conn: AsyncConnection, item: models.Item) -> set[str]:
        """Return computed tags for given item."""
        stmt = sa.select(db_models.ComputedTags.tags).where(
            db_models.ComputedTags.item_id == item.id
        )
        response = (await conn.execute(stmt)).fetchone()
        return set(response.tags) if response else set()

    async def save_computed_tags(
        self,
        conn: AsyncConnection,
        item: models.Item,
        tags: set[str],
    ) -> None:
        """Save computed tags for given item."""
        insert = pg_insert(db_models.ComputedTags).values(item_id=item.id, tags=tuple(tags))

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.ComputedTags.item_id],
            set_={'tags': insert.excluded.tags},
        )

        await conn.execute(stmt)

    async def get_known_tags_anon(self, conn: AsyncConnection) -> dict[str, int]:
        """Return known tags for anon."""
        query = sa.select(db_models.KnownTagsAnon.tag, db_models.KnownTagsAnon.counter).order_by(
            sa.desc(db_models.KnownTagsAnon.counter)
        )

        response = (await conn.execute(query)).fetchall()
        return {row.tag: row.counter for row in response}

    async def get_known_tags_user(
        self,
        conn: AsyncConnection,
        user: models.User,
    ) -> dict[str, int]:
        """Return known tags for specific user."""
        query = (
            sa.select(db_models.KnownTags.tag, db_models.KnownTags.counter)
            .where(db_models.KnownTags.user_id == user.id)
            .order_by(sa.desc(db_models.KnownTags.counter))
        )

        response = (await conn.execute(query)).fetchall()
        return {row.tag: row.counter for row in response}

    async def autocomplete_tag_anon(
        self,
        conn: AsyncConnection,
        tag: str,
        limit: int,
    ) -> list[str]:
        """Autocomplete tag for anon user."""
        query = (
            sa.select(db_models.KnownTagsAnon.tag)
            .where(
                db_models.KnownTagsAnon.tag.ilike(f'%{tag}%'),
                db_models.KnownTagsAnon.counter > 0,
            )
            .order_by(
                sa.desc(db_models.KnownTagsAnon.counter),
                sa.asc(db_models.KnownTagsAnon.tag),
            )
            .limit(limit)
        )

        response = (await conn.execute(query)).fetchall()
        return [row.tag for row in response]

    async def autocomplete_tag_user(
        self,
        conn: AsyncConnection,
        user: models.User,
        tag: str,
        limit: int,
    ) -> list[str]:
        """Autocomplete tag for known user."""
        query = (
            sa.select(db_models.KnownTags.tag)
            .where(
                db_models.KnownTags.tag.ilike(f'%{tag}%'),
                db_models.KnownTags.user_id == user.id,
                db_models.KnownTags.counter > 0,
            )
            .order_by(
                sa.desc(db_models.KnownTags.counter),
                sa.asc(db_models.KnownTags.tag),
            )
            .limit(limit)
        )

        response = (await conn.execute(query)).fetchall()
        return [row.tag for row in response]
