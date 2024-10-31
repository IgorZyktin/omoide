"""Search repository."""

import abc

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.orm import aliased
from sqlalchemy.sql import Select

from omoide import const
from omoide import models
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import queries
from omoide.database.interfaces.abs_search_repo import AbsSearchRepo


class _SearchRepositoryBase(AbsSearchRepo[AsyncConnection], abc.ABC):
    """Base class with helper methods."""

    @staticmethod
    def _expand_query(
        user: models.User,
        query: Select,
        tags_include: set[str],
        tags_exclude: set[str],
        collections: bool,
    ) -> Select:
        """Add access control and filtering."""
        query = query.join(
            db_models.ComputedTags,
            db_models.ComputedTags.item_id == db_models.Item.id,
        )

        query = queries.ensure_user_has_permissions(user, query)

        if tags_include:
            query = query.where(
                db_models.ComputedTags.tags.contains(tuple(tags_include)),
            )

        if tags_exclude:
            query = query.where(
                ~db_models.ComputedTags.tags.overlap(tuple(tags_exclude)),
            )

        if collections:
            query = query.where(db_models.Item.is_collection == sa.true())

        return query

    @staticmethod
    async def _home_base(
        conn: AsyncConnection,
        condition: sa.BinaryExpression | sa.BooleanClauseList,
        order: const.ORDER_TYPE,
        collections: bool,
        direct: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return home items (generic)."""
        query = queries.get_items_with_parent_names().where(condition)

        if collections:
            query = query.where(db_models.Item.is_collection == sa.true())

        if direct:
            query = query.where(db_models.Item.parent_id == sa.null())

        query = queries.apply_order(query, order, last_seen)
        query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row, extra_keys=['parent_name']) for row in response]


class SearchRepo(_SearchRepositoryBase):
    """Repository that performs all search queries."""

    async def count(
        self,
        conn: AsyncConnection,
        user: models.User,
        tags_include: set[str],
        tags_exclude: set[str],
        collections: bool,
    ) -> int:
        """Return total amount of items relevant to this search query."""
        query = sa.select(sa.func.count().label('total_items')).select_from(db_models.Item)

        query = self._expand_query(
            user=user,
            query=query,
            tags_include=tags_include,
            tags_exclude=tags_exclude,
            collections=collections,
        )

        response = (await conn.execute(query)).fetchone()
        return int(response.total_items)

    async def search(
        self,
        conn: AsyncConnection,
        user: models.User,
        tags_include: set[str],
        tags_exclude: set[str],
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items for dynamic load."""
        query = sa.select(db_models.Item)

        query = self._expand_query(
            user=user,
            query=query,
            tags_include=tags_include,
            tags_exclude=tags_exclude,
            collections=collections,
        )

        query = queries.apply_order(
            stmt=query,
            order=order,
            last_seen=last_seen,
        )

        query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row) for row in response]

    async def get_home_items_for_anon(
        self,
        conn: AsyncConnection,
        order: const.ORDER_TYPE,
        collections: bool,
        direct: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return home items for anon."""
        condition = queries.item_is_public()
        return await self._home_base(conn, condition, order, collections, direct, last_seen, limit)

    async def get_home_items_for_known(
        self,
        conn: AsyncConnection,
        user: models.User,
        order: const.ORDER_TYPE,
        collections: bool,
        direct: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return home items for known user."""
        condition = sa.or_(
            db_models.Item.owner_id == user.id,
            db_models.Item.permissions.any(user.id),
        )
        return await self._home_base(conn, condition, order, collections, direct, last_seen, limit)

    async def count_all_tags_anon(self, conn: AsyncConnection) -> dict[str, int]:
        """Return counters for known tags (anon user)."""
        query = sa.select(
            db_models.KnownTagsAnon.tag,
            db_models.KnownTagsAnon.counter,
        ).order_by(
            sa.desc(db_models.KnownTagsAnon.counter),
        )

        response = (await conn.execute(query)).fetchall()
        return {row.tag: row.counter for row in response}

    async def count_all_tags_known(
        self,
        conn: AsyncConnection,
        user: models.User,
    ) -> dict[str, int]:
        """Return counters for known tags (known user)."""
        query = (
            sa.select(
                db_models.KnownTags.tag,
                db_models.KnownTags.counter,
            )
            .where(
                db_models.KnownTags.user_id == user.id,
            )
            .order_by(
                sa.desc(db_models.KnownTags.counter),
            )
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

    async def autocomplete_tag_known(
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
