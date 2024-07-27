"""Browse repository."""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import cast
from sqlalchemy.dialects import postgresql as pg

from omoide import domain
from omoide import models
from omoide.storage import interfaces as storage_interfaces
from omoide.storage.database import db_models
from omoide.storage.interfaces.repositories.abs_users_repo import AbsUsersRepo
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
            user: models.User,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Load all children of an item with given UUID."""
        stmt = sa.select(
            db_models.Item
        ).where(
            db_models.Item.parent_uuid == uuid,
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        stmt = stmt.order_by(
            db_models.Item.number
        ).limit(
            aim.items_per_page
        ).offset(
            aim.offset
        )

        response = await self.db.fetch_all(stmt)
        return [domain.Item(**x) for x in response]

    async def count_children(
            self,
            user: models.User,
            uuid: UUID,
    ) -> int:
        """Count all children of an item with given UUID."""
        stmt = sa.select(
            sa.func.count().label('total_items')
        ).select_from(
            db_models.Item
        ).where(
            db_models.Item.parent_uuid == uuid
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        response = await self.db.fetch_one(stmt)
        return int(response['total_items'])

    async def get_location(
            self,
            user: models.User,
            uuid: UUID,
            aim: domain.Aim,
            users_repo: AbsUsersRepo,
    ) -> Optional[domain.Location]:
        """Return Location of the item."""
        current_item = await self.read_item(uuid)

        if current_item is None:
            return None

        owner = await users_repo.read_user(current_item.owner_uuid)

        if owner is None:
            return None

        ancestors = await self.get_complex_ancestors(
            user=user,
            item=current_item,
            aim=aim,
        )

        return domain.Location(
            owner=owner,
            items=ancestors,
            current_item=current_item,
        )

    async def get_complex_ancestors(
            self,
            user: models.User,
            item: domain.Item,
            aim: domain.Aim,
    ) -> list[domain.PositionedItem]:
        """Return list of positioned ancestors of given item."""
        ancestors = []

        item_uuid = item.parent_uuid
        child_uuid = item.uuid

        while True:
            if item_uuid is None:
                break

            ancestor = await self.get_item_with_position(
                user=user,
                item_uuid=item_uuid,
                child_uuid=child_uuid,
                aim=aim,
            )

            if ancestor is None:
                break

            ancestors.append(ancestor)
            item_uuid = ancestor.item.parent_uuid
            child_uuid = ancestor.item.uuid

        ancestors.reverse()
        return ancestors

    async def get_item_with_position(
            self,
            user: models.User,
            item_uuid: UUID,
            child_uuid: UUID,
            aim: domain.Aim,
    ) -> Optional[domain.PositionedItem]:
        """Return item with its position in siblings."""
        # TODO - rewrite to sqlalchemy
        if user.is_anon:
            query = """
            WITH children AS (
                SELECT uuid
                FROM items
                WHERE parent_uuid = :item_uuid
                ORDER BY number
            )
            SELECT uuid,
                   parent_uuid,
                   owner_uuid,
                   number,
                   name,
                   is_collection,
                   content_ext,
                   preview_ext,
                   thumbnail_ext,
                   tags,
                   (select array_position(array(select uuid from children),
                                          :child_uuid)) as position,
                   (select count(*) from children) as total_items
            FROM items
            WHERE uuid = :item_uuid;
            """
            values = {
                'item_uuid': str(item_uuid),
                'child_uuid': str(child_uuid),
            }
        else:
            query = """
            WITH children AS (
                SELECT uuid
                FROM items
                WHERE parent_uuid = :item_uuid
                AND (:user_uuid = ANY(permissions)
                 OR owner_uuid::text = :user_uuid)
                ORDER BY number
            )
            SELECT uuid,
                   parent_uuid,
                   owner_uuid,
                   number,
                   name,
                   is_collection,
                   content_ext,
                   preview_ext,
                   thumbnail_ext,
                   tags,
                   (select array_position(array(select uuid from children),
                                          :child_uuid)) as position,
                   (select count(*) from children) as total_items
            FROM items
            WHERE uuid = :item_uuid;
            """

            values = {
                'user_uuid': str(user.uuid),
                'item_uuid': str(item_uuid),
                'child_uuid': str(child_uuid),
            }

        response = await self.db.fetch_one(query, values)

        if response is None:
            return None

        mapping = dict(response)

        return domain.PositionedItem(
            position=mapping.pop('position') or 1,
            total_items=mapping.pop('total_items') or 1,
            items_per_page=aim.items_per_page,
            item=domain.Item(**response),
        )

    async def simple_find_items_to_browse(
            self,
            user: models.User,
            uuid: Optional[UUID],
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items using simple request."""
        stmt = sa.select(
            db_models.Item
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        if aim.nested:
            stmt = stmt.where(
                db_models.Item.parent_uuid == uuid
            )

        if aim.ordered:
            stmt = stmt.where(
                db_models.Item.number > aim.last_seen
            ).order_by(
                db_models.Item.number
            )

        else:
            stmt = stmt.order_by(sa.func.random())

        stmt = stmt.limit(aim.items_per_page)

        response = await self.db.fetch_all(stmt)
        return [domain.Item(**x) for x in response]

    async def complex_find_items_to_browse(
            self,
            user: models.User,
            uuid: Optional[UUID],
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items to browse depending on parent (including inheritance)."""
        values = {
            'uuid': str(uuid),
            'limit': aim.items_per_page,
        }

        # TODO - rewrite to sqlalchemy
        if user.is_anon:
            stmt = """
WITH RECURSIVE nested_items AS
       (SELECT items.uuid          AS uuid,
               items.parent_uuid   AS parent_uuid,
               items.owner_uuid    AS owner_uuid,
               items.number        AS number,
               items.name          AS name,
               items.is_collection AS is_collection,
               items.content_ext   AS content_ext,
               items.preview_ext   AS preview_ext,
               items.thumbnail_ext AS thumbnail_ext
        FROM items
        WHERE items.parent_uuid = CAST(:uuid AS uuid)
        UNION
        SELECT items.uuid          AS uuid,
               items.parent_uuid   AS parent_uuid,
               items.owner_uuid    AS owner_uuid,
               items.number        AS number,
               items.name          AS name,
               items.is_collection AS is_collection,
               items.content_ext   AS content_ext,
               items.preview_ext   AS preview_ext,
               items.thumbnail_ext AS thumbnail_ext
        FROM items
                 INNER JOIN nested_items
                            ON items.parent_uuid = nested_items.uuid)
SELECT uuid,
       parent_uuid,
       owner_uuid,
       number,
       name,
       is_collection,
       content_ext,
       preview_ext,
       thumbnail_ext
FROM nested_items
WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
            """
        else:
            stmt = """
WITH RECURSIVE nested_items AS
       (SELECT items.uuid          AS uuid,
               items.parent_uuid   AS parent_uuid,
               items.owner_uuid    AS owner_uuid,
               items.number        AS number,
               items.name          AS name,
               items.is_collection AS is_collection,
               items.content_ext   AS content_ext,
               items.preview_ext   AS preview_ext,
               items.thumbnail_ext AS thumbnail_ext,
               items.permissions   AS permissions
        FROM items
        WHERE items.parent_uuid = CAST(:uuid AS uuid)
        UNION
        SELECT items.uuid          AS uuid,
               items.parent_uuid   AS parent_uuid,
               items.owner_uuid    AS owner_uuid,
               items.number        AS number,
               items.name          AS name,
               items.is_collection AS is_collection,
               items.content_ext   AS content_ext,
               items.preview_ext   AS preview_ext,
               items.thumbnail_ext AS thumbnail_ext,
               items.permissions   AS permissions
        FROM items
                 INNER JOIN nested_items
                            ON items.parent_uuid = nested_items.uuid)
SELECT uuid,
       parent_uuid,
       owner_uuid,
       number,
       name,
       is_collection,
       content_ext,
       preview_ext,
       thumbnail_ext,
       permissions
FROM nested_items
WHERE (owner_uuid = CAST(:user_uuid AS uuid)
    OR CAST(:user_uuid AS TEXT) = ANY(permissions))
            """
            values['user_uuid'] = str(user.uuid)

        if aim.ordered:
            stmt += ' AND number > :last_seen'
            values['last_seen'] = aim.last_seen

        if aim.ordered:
            stmt += ' ORDER BY number'
        else:
            stmt += ' ORDER BY random()'

        stmt += ' LIMIT :limit;'

        response = await self.db.fetch_all(stmt, values)
        return [domain.Item(**x) for x in response]

    # FIXME - delete this method
    async def get_recent_items(
            self,
            user: models.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Return portion of recently loaded items."""
        # TODO - rewrite to sqlalchemy
        stmt = """
        WITH valid_items AS (
            SELECT uuid,
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
                   me.created_at
            FROM items
            LEFT JOIN metainfo me on uuid = me.item_uuid
            WHERE ((owner_uuid = CAST(:user_uuid AS uuid)
                OR CAST(:user_uuid AS TEXT) = ANY(permissions)))
        )
        SELECT uuid,
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
            date(valid_items.created_at) = (
                SELECT max(date(created_at)) FROM valid_items
            )
            AND number > :last_seen
            ORDER BY number
            OFFSET :offset
            LIMIT :limit;
        """
        values = {
            'user_uuid': str(user.uuid),
            'last_seen': aim.last_seen,
            'limit': aim.items_per_page,
            'offset': aim.offset,
        }
        response = await self.db.fetch_all(stmt, values)
        return [domain.Item(**x) for x in response]

    async def get_recently_updated_items(
        self,
        user: models.User,
        last_seen: int,
        limit: int,
    ) -> list[domain.Item]:
        """Return recently updated items."""
        stmt = """
        WITH valid_items AS (
            SELECT uuid,
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
        SELECT uuid,
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

    async def get_parents_names(
            self,
            items: list[domain.Item],
    ) -> list[Optional[str]]:
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
