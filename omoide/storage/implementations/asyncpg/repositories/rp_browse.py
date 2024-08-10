"""Browse repository."""

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import cast
from sqlalchemy.dialects import postgresql as pg

from omoide import const
from omoide import models
from omoide.storage import interfaces as storage_interfaces
from omoide.storage.database import db_models
from omoide.storage.implementations.asyncpg.repositories import queries
from omoide.storage.implementations.asyncpg.repositories.rp_items import (
    ItemsRepo
)


class BrowseRepository(
    storage_interfaces.AbsBrowseRepository,
    ItemsRepo,
):
    """Repository that performs all browse queries."""

    async def get_children(
        self,
        item: models.Item,
        offset: int | None,
        limit: int | None,
    ) -> list[models.Item]:
        """Load all children of given item."""
        stmt = sa.select(
            db_models.Item
        ).where(
            db_models.Item.parent_uuid == item.uuid,
        ).order_by(
            db_models.Item.number
        )

        if offset:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)
        return [models.Item(**x) for x in response]

    async def count_children(self, item: models.Item) -> int:
        """Count all children of an item with given UUID."""
        stmt = sa.select(
            sa.func.count().label('total_items')
        ).select_from(
            db_models.Item
        ).where(
            db_models.Item.parent_uuid == item.uuid
        )

        response = await self.db.fetch_one(stmt)
        return int(response['total_items'])

    async def browse_direct_anon(
        self,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""
        stmt = sa.select(
            db_models.Item
        ).where(
            db_models.Item.owner_uuid.in_(  # noqa
                sa.select(db_models.PublicUsers.user_uuid)
            ),
            db_models.Item.parent_uuid == item_uuid,
        )

        if collections:
            stmt = stmt.where(db_models.Item.is_collection == True)  # noqa

        stmt = queries.apply_order(stmt, order, last_seen)
        stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)
        return [models.Item(**row) for row in response]

    async def browse_direct_known(
        self,
        user: models.User,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""
        stmt = sa.select(
            db_models.Item
        ).where(
            sa.or_(
                db_models.Item.owner_uuid.in_(  # noqa
                    sa.select(db_models.PublicUsers.user_uuid)
                ),
                db_models.Item.owner_uuid == user.uuid,
                db_models.Item.permissions.any(str(user.uuid)),
            ),
            db_models.Item.parent_uuid == item_uuid,
        )

        if collections:
            stmt = stmt.where(db_models.Item.is_collection == True)  # noqa

        stmt = queries.apply_order(stmt, order, last_seen)
        stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)
        return [models.Item(**row) for row in response]

    async def browse_related_anon(
        self,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""
        stmt = """
    WITH RECURSIVE nested_items AS
           (SELECT items.id            AS id,
                   items.uuid          AS uuid,
                   items.parent_uuid   AS parent_uuid,
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
            WHERE items.parent_uuid = CAST(:item_uuid AS uuid)
            UNION
            SELECT items.id            AS id,
                   items.uuid          AS uuid,
                   items.parent_uuid   AS parent_uuid,
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
                                ON items.parent_uuid = nested_items.uuid)
    SELECT id,
           uuid,
           parent_uuid,
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
    WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
        """

        values = {
            'item_uuid': str(item_uuid),
            'limit': limit,
        }

        if collections:
            stmt += ' AND is_collection = True'

        if order == const.ASC:
            stmt += ' AND number > :last_seen'
            stmt += ' ORDER BY number'
            values['last_seen'] = last_seen
        elif order == const.DESC:
            stmt += ' AND number < :last_seen'
            stmt += ' ORDER BY number'
            values['last_seen'] = last_seen
        else:
            stmt += ' ORDER BY random()'

        stmt += ' LIMIT :limit;'

        response = await self.db.fetch_all(stmt, values)
        return [models.Item(**x) for x in response]

    async def browse_related_known(
        self,
        user: models.User,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""
        stmt = """
    WITH RECURSIVE nested_items AS
           (SELECT items.id            AS id,
                   items.uuid          AS uuid,
                   items.parent_uuid   AS parent_uuid,
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
            WHERE items.parent_uuid = CAST(:item_uuid AS uuid)
            UNION
            SELECT items.id            AS id,
                   items.uuid          AS uuid,
                   items.parent_uuid   AS parent_uuid,
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
                                ON items.parent_uuid = nested_items.uuid)
    SELECT id,
           uuid,
           parent_uuid,
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
    WHERE ((owner_uuid IN (SELECT user_uuid FROM public_users))
        OR (owner_uuid = CAST(:user_uuid AS uuid))
        OR CAST(:user_uuid AS TEXT) = ANY(permissions))
        """

        values = {
            'user_uuid': str(user.uuid),
            'item_uuid': str(item_uuid),
            'limit': limit,
        }

        if collections:
            stmt += ' AND is_collection = True'

        if order == const.ASC:
            stmt += ' AND number > :last_seen'
            stmt += ' ORDER BY number'
            values['last_seen'] = last_seen
        elif order == const.DESC:
            stmt += ' AND number < :last_seen'
            stmt += ' ORDER BY number'
            values['last_seen'] = last_seen
        else:
            stmt += ' ORDER BY random()'

        stmt += ' LIMIT :limit;'

        response = await self.db.fetch_all(stmt, values)
        return [models.Item(**row) for row in response]

    async def get_recently_updated_items(
        self,
        user: models.User,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return recently updated items."""
        stmt = """
        WITH valid_items AS (
            SELECT id,
                   uuid,
                   parent_uuid,
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
            LEFT JOIN metainfo me on uuid = me.item_uuid
            WHERE ((owner_uuid = CAST(:user_uuid AS uuid)
                OR CAST(:user_uuid AS TEXT) = ANY(permissions)))
        )
        SELECT id,
               uuid,
               parent_uuid,
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
            AND number > :last_seen
            ORDER BY number
            LIMIT :limit;
        """
        values = {
            'user_uuid': str(user.uuid),
            'last_seen': last_seen,
            'limit': limit,
        }
        response = await self.db.fetch_all(stmt, values)
        return [models.Item(**x) for x in response]

    async def get_parent_names(
        self,
        items: list[models.Item],
    ) -> list[str | None]:
        """Get names of parents of the given items."""
        uuids = [
            str(x.parent_uuid)
            if x.parent_uuid else None
            for x in items
        ]

        subquery = sa.select(
            sa.func.unnest(
                cast(uuids, pg.ARRAY(sa.Text))  # type: ignore
            ).label('uuid')
        ).subquery('given_uuid')

        stmt = sa.select(
            subquery.c.uuid, db_models.Item.name
        ).join(
            db_models.Item,
            db_models.Item.uuid == cast(subquery.c.uuid, pg.UUID),
            isouter=True,
        )

        response = await self.db.fetch_all(stmt)
        return [record['name'] for record in response]
