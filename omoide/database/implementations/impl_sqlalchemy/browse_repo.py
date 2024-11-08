"""Browse repository."""

import abc

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.orm import aliased

from omoide import const
from omoide import models
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import queries
from omoide.database.interfaces.abs_browse_repo import AbsBrowseRepo


class _BrowseRepoBase(AbsBrowseRepo[AsyncConnection], abc.ABC):
    """Base class with helper methods."""

    @staticmethod
    async def _browse_base(
        conn: AsyncConnection,
        condition: sa.BinaryExpression | sa.BooleanClauseList | sa.ColumnElement,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return browse items (generic)."""
        query = queries.get_items_with_parent_names().where(condition)

        if plan.collections:
            query = query.where(db_models.Item.is_collection == sa.true())

        query = queries.finalize_query(query, plan)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row, extra_keys=['parent_name']) for row in response]


class BrowseRepo(_BrowseRepoBase):
    """Repository that performs all browse queries."""

    async def browse_direct_anon(
        self,
        conn: AsyncConnection,
        item: models.Item,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""
        condition = sa.and_(
            queries.item_is_public(),
            db_models.Item.parent_id == item.id,
        )
        return await self._browse_base(conn, condition, plan)

    async def browse_direct_known(
        self,
        conn: AsyncConnection,
        user: models.User,
        item: models.Item,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""
        condition = sa.and_(
            sa.or_(
                queries.item_is_public(),
                db_models.Item.owner_id == user.id,
                db_models.Item.permissions.any_() == user.id,
            ),
            db_models.Item.parent_id == item.id,
        )
        return await self._browse_base(conn, condition, plan)

    async def browse_related_anon(
        self,
        conn: AsyncConnection,
        item: models.Item,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""
        query = """
    WITH RECURSIVE nested_items AS
           (SELECT items.id            AS id,
                   items.uuid          AS uuid,
                   items.parent_id     AS parent_id,
                   items.parent_uuid   AS parent_uuid,
                   items.owner_id      AS owner_id,
                   items.owner_uuid    AS owner_uuid,
                   items.number        AS number,
                   items.name          AS name,
                   items.status        AS status,
                   items.is_collection AS is_collection,
                   items.content_ext   AS content_ext,
                   items.preview_ext   AS preview_ext,
                   items.thumbnail_ext AS thumbnail_ext,
                   items.tags          AS tags,
                   items.permissions   AS permissions
            FROM items
            WHERE items.parent_id = :item_id
            UNION
            SELECT items.id            AS id,
                   items.uuid          AS uuid,
                   items.parent_id     AS parent_id,
                   items.parent_uuid   AS parent_uuid,
                   items.owner_id      AS owner_id,
                   items.owner_uuid    AS owner_uuid,
                   items.number        AS number,
                   items.name          AS name,
                   items.status        AS status,
                   items.is_collection AS is_collection,
                   items.content_ext   AS content_ext,
                   items.preview_ext   AS preview_ext,
                   items.thumbnail_ext AS thumbnail_ext,
                   items.tags          AS tags,
                   items.permissions   AS permissions
            FROM items
                     INNER JOIN nested_items
                                ON items.parent_id = nested_items.id)
    SELECT nested_items.id,
           nested_items.uuid,
           nested_items.parent_id,
           nested_items.parent_uuid,
           nested_items.owner_id,
           nested_items.owner_uuid,
           nested_items.number,
           nested_items.name,
           nested_items.status,
           nested_items.is_collection,
           nested_items.content_ext,
           nested_items.preview_ext,
           nested_items.thumbnail_ext,
           nested_items.tags,
           nested_items.permissions,
           i2.name as parent_name
    FROM nested_items
    LEFT JOIN items i2 ON nested_items.parent_id = i2.id
    WHERE nested_items.owner_id IN (SELECT id FROM users WHERE is_public)
      AND nested_items.status = :status
        """

        values = {
            'item_id': item.id,
            'limit': plan.limit,
            'status': models.Status.AVAILABLE.value,
        }

        if plan.collections:
            query += ' AND nested_items.is_collection = True'

        if plan.order == const.ASC:
            query += ' AND nested_items.number > :last_seen'
            query += ' ORDER BY nested_items.number'
            values['last_seen'] = plan.last_seen or -1
        elif plan.order == const.DESC:
            query += ' AND nested_items.number < :last_seen'
            query += ' ORDER BY nested_items.number'
            values['last_seen'] = plan.last_seen or -1
        else:
            query += ' ORDER BY random()'

        query += ' LIMIT :limit;'

        response = (await conn.execute(sa.text(query), values)).fetchall()
        return [models.Item.from_obj(row, extra_keys=['parent_name']) for row in response]

    async def browse_related_known(
        self,
        conn: AsyncConnection,
        user: models.User,
        item: models.Item,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""
        query = """
    WITH RECURSIVE nested_items AS
           (SELECT items.id            AS id,
                   items.uuid          AS uuid,
                   items.parent_id     AS parent_id,
                   items.parent_uuid   AS parent_uuid,
                   items.owner_id      AS owner_id,
                   items.owner_uuid    AS owner_uuid,
                   items.number        AS number,
                   items.name          AS name,
                   items.status        AS status,
                   items.is_collection AS is_collection,
                   items.content_ext   AS content_ext,
                   items.preview_ext   AS preview_ext,
                   items.thumbnail_ext AS thumbnail_ext,
                   items.tags          AS tags,
                   items.permissions   AS permissions
            FROM items
            WHERE items.parent_id = :item_id
            UNION
            SELECT items.id            AS id,
                   items.uuid          AS uuid,
                   items.parent_id     AS parent_id,
                   items.parent_uuid   AS parent_uuid,
                   items.owner_id      AS owner_id,
                   items.owner_uuid    AS owner_uuid,
                   items.number        AS number,
                   items.name          AS name,
                   items.status        AS status,
                   items.is_collection AS is_collection,
                   items.content_ext   AS content_ext,
                   items.preview_ext   AS preview_ext,
                   items.thumbnail_ext AS thumbnail_ext,
                   items.tags          AS tags,
                   items.permissions   AS permissions
            FROM items
                     INNER JOIN nested_items
                                ON items.parent_id = nested_items.id)
    SELECT nested_items.id,
           nested_items.uuid,
           nested_items.parent_id,
           nested_items.parent_uuid,
           nested_items.owner_id,
           nested_items.owner_uuid,
           nested_items.number,
           nested_items.name,
           nested_items.status,
           nested_items.is_collection,
           nested_items.content_ext,
           nested_items.preview_ext,
           nested_items.thumbnail_ext,
           nested_items.tags,
           nested_items.permissions,
           i2.name as parent_name
    FROM nested_items
    LEFT JOIN items i2 ON nested_items.parent_id = i2.id
    WHERE nested_items.status = :status
      AND (
        nested_items.owner_id IN (SELECT id FROM users WHERE is_public)
        OR nested_items.owner_id = :user_id
        OR :user_id = ANY(nested_items.permissions)
      )
        """

        values = {
            'user_id': user.id,
            'item_id': item.id,
            'status': models.Status.AVAILABLE.value,
            'limit': plan.limit,
        }

        if plan.collections:
            query += ' AND nested_items.is_collection = True'

        if plan.order == const.ASC:
            query += ' AND nested_items.number > :last_seen'
            query += ' ORDER BY nested_items.number'
            values['last_seen'] = plan.last_seen or -1
        elif plan.order == const.DESC:
            query += ' AND nested_items.number < :last_seen'
            query += ' ORDER BY nested_items.number'
            values['last_seen'] = plan.last_seen or -1
        else:
            query += ' ORDER BY random()'

        query += ' LIMIT :limit;'

        response = (await conn.execute(sa.text(query), values)).fetchall()
        return [models.Item.from_obj(row, extra_keys=['parent_name']) for row in response]

    async def get_recently_updated_items(
        self,
        conn: AsyncConnection,
        user: models.User,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return recently updated items."""
        parents = aliased(db_models.Item)
        query = (
            sa.select(
                db_models.Item,
                db_models.Metainfo.updated_at,
                sa.func.coalesce(parents.name, db_models.Item.name).label('parent_name'),
            )
            .join(parents, parents.id == db_models.Item.parent_id, isouter=True)
            .join(db_models.Metainfo, db_models.Metainfo.item_id == db_models.Item.id)
            .where(
                sa.or_(
                    db_models.Item.owner_id == user.id,
                    db_models.Item.permissions.any_() == user.id,
                ),
                db_models.Item.status != models.Status.DELETED,
            )
        )

        if plan.collections:
            query = query.where(db_models.Item.is_collection == sa.true())

        if plan.last_seen and plan.last_seen != -1:
            query = query.where(db_models.Item.number < plan.last_seen)

        query = query.order_by(
            sa.desc(db_models.Metainfo.updated_at),
            sa.desc(db_models.Item.number),
        ).limit(plan.limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row, extra_keys=['parent_name']) for row in response]
