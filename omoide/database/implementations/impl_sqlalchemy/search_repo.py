"""Search repository."""

import abc

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection
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
        condition: sa.BinaryExpression | sa.BooleanClauseList | sa.ColumnElement,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return home items (generic)."""
        query = queries.get_items_with_parent_names().where(condition)
        query = query.where(db_models.Item.status != models.Status.DELETED)

        if plan.collections:
            query = query.where(db_models.Item.is_collection == sa.true())

        if plan.direct:
            query = query.where(db_models.Item.parent_id == sa.null())

        query = queries.apply_order(query, plan.order, plan.last_seen)
        query = query.limit(plan.limit)

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
        return int(response.total_items) if response else 0

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
        query = queries.get_items_with_parent_names()

        query = self._expand_query(
            user=user,
            query=query,
            tags_include=tags_include,
            tags_exclude=tags_exclude,
            collections=collections,
        )

        query = queries.apply_order(query, order, last_seen)
        query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row, extra_keys=['parent_name']) for row in response]

    async def get_home_items_for_anon(
        self,
        conn: AsyncConnection,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return home items for anon."""
        condition = queries.item_is_public()
        return await self._home_base(conn, condition, plan)

    async def get_home_items_for_known(
        self,
        conn: AsyncConnection,
        user: models.User,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return home items for known user."""
        condition = sa.or_(
            db_models.Item.owner_id == user.id,
            db_models.Item.permissions.any_() == user.id,
        )
        return await self._home_base(conn, condition, plan)
