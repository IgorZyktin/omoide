"""Browse repository."""


import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import const
from omoide import models
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import queries
from omoide.database.interfaces.abs_browse_repo import AbsBrowseRepo


class BrowseRepo(AbsBrowseRepo[AsyncConnection]):
    """Repository that performs all browse queries."""

    async def get_children(
        self,
        conn: AsyncConnection,
        item: models.Item,
        offset: int | None,
        limit: int | None,
    ) -> list[models.Item]:
        """Load all children of given item."""
        query = (
            sa.select(db_models.Item)
            .where(
                db_models.Item.parent_uuid == item.uuid,
            )
            .order_by(db_models.Item.number)
        )

        if offset:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row) for row in response]

    async def browse_direct_anon(
        self,
        conn: AsyncConnection,
        item: models.Item,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""
        query = sa.select(db_models.Item).where(
            queries.item_is_public(),
            db_models.Item.parent_id == item.id,
        )

        if collections:
            query = query.where(db_models.Item.is_collection == sa.true())

        query = queries.apply_order(query, order, last_seen)
        query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row) for row in response]

    async def browse_direct_known(
        self,
        conn: AsyncConnection,
        user: models.User,
        item: models.Item,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""
        query = sa.select(db_models.Item).where(
            sa.or_(
                queries.item_is_public(),
                db_models.Item.owner_id == user.id,
                db_models.Item.permissions.any(user.id),
            ),
            db_models.Item.parent_id == item.id,
        )

        if collections:
            query = query.where(db_models.Item.is_collection == sa.true())

        query = queries.apply_order(query, order, last_seen)
        query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row) for row in response]

    async def browse_related_anon(
        self,
        conn: AsyncConnection,
        item: models.Item,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
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
                   items.is_collection AS is_collection,
                   items.content_ext   AS content_ext,
                   items.preview_ext   AS preview_ext,
                   items.thumbnail_ext AS thumbnail_ext,
                   items.tags          AS tags,
                   items.permissions   AS permissions
            FROM items
                     INNER JOIN nested_items
                                ON items.parent_id = nested_items.id)
    SELECT id,
           uuid,
           parent_id,
           parent_uuid,
           owner_id,
           owner_uuid,
           number,
           name,
           is_collection,
           content_ext,
           preview_ext,
           thumbnail_ext,
           tags,
           permissions
    FROM nested_items
    WHERE owner_id IN (SELECT id FROM users WHERE is_public)
        """

        values = {
            'item_id': item.id,
            'limit': limit,
        }

        if collections:
            query += ' AND is_collection = True'

        if order == const.ASC:
            query += ' AND number > :last_seen'
            query += ' ORDER BY number'
            values['last_seen'] = last_seen
        elif order == const.DESC:
            query += ' AND number < :last_seen'
            query += ' ORDER BY number'
            values['last_seen'] = last_seen
        else:
            query += ' ORDER BY random()'

        query += ' LIMIT :limit;'

        response = (await conn.execute(sa.text(query), values)).fetchall()
        return [models.Item.from_obj(row) for row in response]

    async def browse_related_known(
        self,
        conn: AsyncConnection,
        user: models.User,
        item: models.Item,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
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
                   items.is_collection AS is_collection,
                   items.content_ext   AS content_ext,
                   items.preview_ext   AS preview_ext,
                   items.thumbnail_ext AS thumbnail_ext,
                   items.tags          AS tags,
                   items.permissions   AS permissions
            FROM items
                     INNER JOIN nested_items
                                ON items.parent_id = nested_items.id)
    SELECT id,
           uuid,
           parent_id,
           parent_uuid,
           owner_id,
           owner_uuid,
           number,
           name,
           is_collection,
           content_ext,
           preview_ext,
           thumbnail_ext,
           tags,
           permissions
    FROM nested_items
    WHERE (owner_id IN (SELECT id FROM users WHERE is_public)
        OR owner_id = :user_id
        OR :user_id = ANY(permissions)
        """

        values = {
            'user_id': user.id,
            'item_id': item.id,
            'limit': limit,
        }

        if collections:
            query += ' AND is_collection = True'

        if order == const.ASC:
            query += ' AND number > :last_seen'
            query += ' ORDER BY number'
            values['last_seen'] = last_seen
        elif order == const.DESC:
            query += ' AND number < :last_seen'
            query += ' ORDER BY number'
            values['last_seen'] = last_seen
        else:
            query += ' ORDER BY random()'

        query += ' LIMIT :limit;'

        response = (await conn.execute(sa.text(query), values)).fetchall()
        return [models.Item.from_obj(row) for row in response]

    async def get_recently_updated_items(
        self,
        conn: AsyncConnection,
        user: models.User,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return recently updated items."""
        query = """
        WITH valid_items AS (
            SELECT id,
                   uuid,
                   parent_id,
                   parent_uuid,
                   owner_id,
                   owner_uuid,
                   number,
                   name,
                   is_collection,
                   content_ext,
                   preview_ext,
                   thumbnail_ext,
                   tags,
                   permissions,
                   me.updated_at
            FROM items
            LEFT JOIN item_metainfo me on id = me.item_id
            WHERE (owner_id = :user_id OR :user_id = ANY(permissions))
        )
        SELECT id,
               uuid,
               parent_id,
               parent_uuid,
               owner_id,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext,
               tags,
               permissions
        FROM valid_items
        WHERE
            date(valid_items.updated_at) = (
                SELECT max(date(updated_at)) FROM valid_items
            )
        """

        values = {
            'user_id': user.id,
            'limit': limit,
        }

        if collections:
            query += ' AND is_collection = True'

        if order == const.ASC:
            query += ' AND number > :last_seen'
            query += ' ORDER BY number'
            values['last_seen'] = last_seen
        elif order == const.DESC:
            query += ' AND number < :last_seen'
            query += ' ORDER BY number'
            values['last_seen'] = last_seen
        else:
            query += ' ORDER BY random()'

        query += ' LIMIT :limit;'

        response = (await conn.execute(sa.text(query), values)).fetchall()
        return [models.Item.from_obj(row) for row in response]
