# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
from typing import Awaitable
from typing import Callable
from typing import Optional
from uuid import UUID
from uuid import uuid4

import sqlalchemy
from sqlalchemy import func

from omoide import domain
from omoide.domain import exceptions
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.presentation import api_models
from omoide.storage import repositories as repo_implementations
from omoide.storage.database import models


class ItemsRepository(
    repo_implementations.BaseRepository,
    repo_interfaces.AbsItemsRepository,
):
    """Repository that perform CRUD operations on items and their data."""

    async def generate_uuid(self) -> UUID:
        """Generate new UUID4 for an item."""
        # TODO(i.zyktin): must also check zombies table
        stmt = """
        SELECT 1 FROM items WHERE uuid = :uuid;
        """
        while True:
            uuid = uuid4()
            exists = await self.db.fetch_one(stmt, {'uuid': uuid})

            if not exists:
                return uuid

    async def check_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Check access to the item."""
        query = """
        SELECT owner_uuid,
               exists(SELECT 1
                      FROM public_users pu
                      WHERE pu.user_uuid = i.owner_uuid)  AS is_public,
               (SELECT :user_uuid = ANY (cp.permissions)) AS is_permitted,
               owner_uuid::text = :user_uuid AS is_owner
        FROM items i
                 LEFT JOIN computed_permissions cp ON cp.item_uuid = i.uuid
        WHERE uuid = :uuid;
        """

        values = {
            'user_uuid': user.uuid,
            'uuid': uuid,
        }
        response = await self.db.fetch_one(query, values)

        if response is None:
            return domain.AccessStatus.not_found()

        return domain.AccessStatus(
            exists=True,
            is_public=bool(response['is_public']),
            is_permitted=bool(response['is_permitted']),
            is_owner=bool(response['is_owner']),
        )

    async def assert_has_access(
            self,
            user: domain.User,
            uuid: UUID,
            only_for_owner: bool,
    ) -> None:
        """Raise if item does not exist or user has no access to it."""
        access = await self.check_access(user, uuid)

        if access.does_not_exist:
            raise exceptions.NotFound(f'Item {uuid} does not exist')

        if access.is_not_given:
            if user.is_anon():
                raise exceptions.Unauthorized(
                    f'Anon user has no access to {uuid}'
                )
            else:
                raise exceptions.Forbidden(
                    f'User {user.uuid} ({user.name}) '
                    f'has no access to {uuid}'
                )

        if access.is_not_owner and only_for_owner:
            raise exceptions.Forbidden(f'You must own item {uuid} '
                                       'to be able to modify it')

    async def create_item(
            self,
            user: domain.User,
            payload: api_models.CreateItemIn,
    ) -> UUID:
        """Create item and return UUID."""
        # TODO - rewrite to sqlalchemy
        stmt = """
        INSERT INTO items (
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
        )
        SELECT
            :uuid,
            :parent_uuid,
            :owner_uuid,
            max(number) + 1 as new_number,
            :name,
            :is_collection,
            NULL,
            NULL,
            NULL,
            :tags,
            :permissions
        FROM items
        RETURNING uuid;
        """

        values = {
            'uuid': payload.uuid,
            'parent_uuid': payload.parent_uuid,
            'owner_uuid': user.uuid,
            'name': payload.name,
            'is_collection': payload.is_collection,
            'tags': payload.tags,
            'permissions': payload.permissions,
        }

        return await self.db.execute(stmt, values)

    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return item or None."""
        stmt = sqlalchemy.select(
            models.Item
        ).where(
            models.Item.uuid == uuid
        )

        response = await self.db.fetch_one(stmt)

        return domain.Item(**response) if response else None

    async def read_children(
            self,
            uuid: UUID,
    ) -> list[domain.Item]:
        """Return all direct descendants of the given item."""
        stmt = """
        SELECT uuid,
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext
        FROM items
        WHERE parent_uuid = :uuid;
        """

        response = await self.db.fetch_all(stmt, {'uuid': uuid})
        return [domain.Item.from_map(each) for each in response]

    async def update_item(
            self,
            item: domain.Item,
    ) -> UUID:
        """Update existing item."""
        stmt = """
        UPDATE items SET
            parent_uuid = :parent_uuid,
            name = :name,
            is_collection = :is_collection,
            content_ext = :content_ext,
            preview_ext = :preview_ext,
            thumbnail_ext = :thumbnail_ext,
            tags = :tags,
            permissions = :permissions
        WHERE uuid = :uuid;
        """

        values = {
            'uuid': item.uuid,
            'parent_uuid': item.parent_uuid,
            'name': item.name,
            'is_collection': item.is_collection,
            'content_ext': item.content_ext,
            'preview_ext': item.preview_ext,
            'thumbnail_ext': item.thumbnail_ext,
            'tags': item.tags,
            'permissions': item.permissions,
        }

        return await self.db.execute(stmt, values)

    async def delete_item(
            self,
            uuid: UUID,
    ) -> bool:
        """Delete item with given UUID."""
        stmt = sqlalchemy.delete(
            models.Item
        ).where(
            models.Item.uuid == uuid
        ).returning(1)

        response = await self.db.fetch_one(stmt)

        return response is not None

    async def count_all_children(
            self,
            uuid: UUID,
    ) -> int:
        """Count dependant items (including the parent itself)."""
        stmt = """
        WITH RECURSIVE nested_items AS (
            SELECT parent_uuid,
                   uuid
            FROM items
            WHERE uuid = :uuid
            UNION ALL
            SELECT i.parent_uuid,
                   i.uuid
            FROM items i
                     INNER JOIN nested_items it2 ON i.parent_uuid = it2.uuid
        )
        SELECT count(*) AS total
        FROM nested_items;
        """

        response = await self.db.fetch_one(stmt, {'uuid': uuid})

        if response is None:
            return 0

        return response['total']

    async def get_simple_location(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
    ) -> Optional[domain.SimpleLocation]:
        """Return Location of the item (without pagination)."""
        ancestors = await self.get_simple_ancestors(item)
        return domain.SimpleLocation(items=ancestors + [item])

    async def get_simple_ancestors(
            self,
            item: domain.Item,
    ) -> list[domain.Item]:
        """Return list of ancestors for given item."""
        # TODO(i.zyktin): what if user has no access
        #  to the item in the middle of dependence chain?

        ancestors = []
        item_uuid = item.parent_uuid

        while True:
            if item_uuid is None:
                break

            ancestor = await self.read_item(item_uuid)

            if ancestor is None:
                break

            ancestors.append(ancestor)
            item_uuid = ancestor.parent_uuid

        ancestors.reverse()
        return ancestors

    async def simple_find_items_to_browse(
            self,
            user: domain.User,
            uuid: Optional[UUID],
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items using simple request."""
        if user.is_anon():
            subquery = sqlalchemy.select(models.PublicUsers.user_uuid)
            conditions = [
                models.Item.owner_uuid.in_(subquery)  # noqa
            ]

        else:
            conditions = []

        if aim.nested:
            conditions.append(models.Item.parent_uuid == uuid)  # noqa

        if aim.ordered:
            conditions.append(models.Item.number > aim.last_seen)

        stmt = sqlalchemy.select(models.Item)

        if conditions:
            stmt = stmt.where(*conditions)

        if user.is_not_anon():
            stmt = stmt.select_from(
                models.Item.__table__.join(
                    models.ComputedPermissions,
                    models.Item.uuid == models.ComputedPermissions.item_uuid,
                    isouter=True,
                )
            ).where(
                sqlalchemy.or_(
                    models.Item.owner_uuid == user.uuid,
                    models.ComputedPermissions.permissions.any(user.uuid),
                )
            )

        if aim.ordered:
            stmt = stmt.order_by(models.Item.number)
        else:
            stmt = stmt.order_by(sqlalchemy.func.random())

        stmt = stmt.limit(aim.items_per_page)

        response = await self.db.fetch_all(stmt)
        # TODO - damn asyncpg tries to bee too smart
        items = [
            domain.Item.from_map(dict(zip(row.keys(), row.values())))
            for row in response
        ]

        return items

    async def complex_find_items_to_browse(
            self,
            user: domain.User,
            uuid: Optional[UUID],
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items to browse depending on parent (including inheritance)."""
        values = {
            'uuid': uuid,
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
            values['user_uuid'] = user.uuid

        if aim.ordered:
            stmt += ' AND number > :last_seen'
            values['last_seen'] = aim.last_seen

        if aim.ordered:
            stmt += ' ORDER BY number'
        else:
            stmt += ' ORDER BY random()'

        stmt += ' LIMIT :limit;'

        response = await self.db.fetch_all(stmt, values)
        # TODO - damn asyncpg tries to bee too smart
        items = [
            domain.Item.from_map(dict(zip(row.keys(), row.values())))
            for row in response
        ]
        return items

    async def update_tags_in_children(
            self,
            item: domain.Item,
    ) -> None:
        """Apply parent tags to every item (and their children too)."""

        async def _update_tags(
                _self: ItemsRepository,
                _item: domain.Item,
        ) -> None:
            """Call DB function that updated everything."""
            # Feature: this operation will recalculate same things
            # many times. Possible place for an optimisation.
            await _self.db.execute(
                sqlalchemy.select(func.compute_tags(_item.uuid))
            )

        await self.apply_downwards(
            item=item,
            already_seen_items=set(),
            # FIXME: use UUID here instead of str
            skip_items={item.uuid},  # noqa
            parent_first=True,
            function=_update_tags,
        )

    async def apply_downwards(
            self,
            item: domain.Item,
            already_seen_items: set[UUID],
            skip_items: set[UUID],
            parent_first: bool,
            function: Callable[['ItemsRepository',
                                domain.Item], Awaitable[None]],
    ) -> None:
        """Apply given function to every descendant item.

        Use cases:
            * We're doing something like delete. Therefore, we must
              delete all children and then their parents.

            * We're doing something like update. Therefore, we must
              update all parents and then their children.
        """
        if item.uuid in already_seen_items:
            return

        # FIXME: use UUID here instead of str
        already_seen_items.add(item.uuid)  # noqa

        if parent_first and item.uuid not in skip_items:
            await function(self, item)

        # FIXME: use UUID here instead of str
        children = await self.read_children(item.uuid)  # noqa

        for child in children:
            await self.apply_downwards(
                item=child,
                already_seen_items=already_seen_items,
                skip_items=skip_items,
                parent_first=parent_first,
                function=function,
            )

        if not parent_first and item.uuid not in skip_items:
            await function(self, item)
