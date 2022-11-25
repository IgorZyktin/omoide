# -*- coding: utf-8 -*-
"""Browse repository.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.domain.interfaces.in_storage \
    .in_repositories.in_rp_browse import AbsBrowseRepository
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg \
    .rp_items_read import ItemsReadRepository


class BrowseRepository(
    AbsBrowseRepository,
    ItemsReadRepository,
):
    """Repository that performs all browse queries."""

    async def get_children(
            self,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Load all children and sub children of the record."""
        stmt = sa.select(
            models.Item
        ).where(
            models.Item.parent_uuid == str(uuid),
            models.Item.uuid != str(uuid),
        ).order_by(
            models.Item.number
        ).limit(
            aim.items_per_page
        ).offset(
            aim.offset
        )
        response = await self.db.fetch_all(stmt)
        return [domain.Item(**x) for x in response]

    async def count_items(
            self,
            uuid: UUID,
    ) -> int:
        """Count all children with all required fields."""
        query = """
        SELECT count(*) AS total_items
        FROM items
        WHERE parent_uuid = :uuid;
        """

        response = await self.db.fetch_one(query, {'uuid': str(uuid)})
        return int(response['total_items'])

    async def get_specific_children(
            self,
            user: domain.User,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Load all children with all required fields (and access)."""
        _query = """
        SELECT uuid,
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE parent_uuid = :item_uuid
            AND uuid <> :item_uuid
            AND (:user_uuid = ANY(cp.permissions)
                 OR it.owner_uuid::text = :user_uuid)
        ORDER BY number
        LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': str(user.uuid),
            'item_uuid': str(uuid),
            'limit': aim.items_per_page,
            'offset': aim.offset,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item(**x) for x in response]

    async def count_specific_items(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> int:
        """Count all children with all required fields (and access)."""
        query = """
        SELECT count(*) AS total_items
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE parent_uuid = :item_uuid
            AND (:user_uuid = ANY(cp.permissions)
                 OR it.owner_uuid::text = :user_uuid);
        """

        values = {
            'user_uuid': str(user.uuid),
            'item_uuid': str(uuid),
        }

        response = await self.db.fetch_one(query, values)
        return int(response['total_items'])

    async def get_location(
            self,
            user: domain.User,
            uuid: UUID,
            aim: domain.Aim,
            users_repo: interfaces.AbsUsersReadRepository,
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
            user: domain.User,
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
            user: domain.User,
            item_uuid: UUID,
            child_uuid: UUID,
            aim: domain.Aim,
    ) -> Optional[domain.PositionedItem]:
        """Return item with its position in siblings."""
        if user.is_anon():
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
                FROM items it
                RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
                WHERE parent_uuid = :item_uuid
                AND (:user_uuid = ANY(cp.permissions)
                 OR it.owner_uuid::text = :user_uuid)
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
            user: domain.User,
            uuid: Optional[UUID],
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items using simple request."""
        if user.is_anon():
            subquery = sa.select(models.PublicUsers.user_uuid)
            conditions = [
                models.Item.owner_uuid.in_(subquery)  # noqa
            ]

        else:
            conditions = []

        s_uuid = str(uuid) if uuid is not None else None

        if aim.nested:
            conditions.append(models.Item.parent_uuid == s_uuid)  # noqa

        if aim.ordered:
            conditions.append(models.Item.number > aim.last_seen)

        stmt = sa.select(models.Item)

        if conditions:
            stmt = stmt.where(*conditions)

        if user.is_not_anon():
            stmt = stmt.select_from(
                models.Item.__table__.join(
                    models.ComputedPermissions,  # type: ignore
                    models.Item.uuid == models.ComputedPermissions.item_uuid,
                    isouter=True,
                )
            ).where(
                sa.or_(
                    models.Item.owner_uuid == str(user.uuid),
                    models.ComputedPermissions.permissions.any(str(user.uuid)),
                )
            )

        if aim.ordered:
            stmt = stmt.order_by(models.Item.number)
        else:
            stmt = stmt.order_by(sa.func.random())

        stmt = stmt.limit(aim.items_per_page)

        response = await self.db.fetch_all(stmt)
        return [domain.Item(**x) for x in response]

    async def complex_find_items_to_browse(
            self,
            user: domain.User,
            uuid: Optional[UUID],
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items to browse depending on parent (including inheritance)."""
        values = {
            'uuid': str(uuid),
            'limit': aim.items_per_page,
        }

        if user.is_anon():
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
SELECT *
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
SELECT *
FROM nested_items
LEFT JOIN computed_permissions cp ON cp.item_uuid = uuid
WHERE (owner_uuid = CAST(:user_uuid AS uuid)
    OR CAST(:user_uuid AS TEXT) = ANY(cp.permissions))
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
