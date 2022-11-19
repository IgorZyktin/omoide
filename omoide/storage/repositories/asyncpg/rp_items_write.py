# -*- coding: utf-8 -*-
"""Repository that performs write operations on items.
"""
import time
from typing import Awaitable
from typing import Callable
from uuid import UUID
from uuid import uuid4

import sqlalchemy

from omoide import domain
from omoide.domain import interfaces
from omoide.presentation import api_models
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg.rp_items_read import \
    ItemsReadRepository


class ItemsWriteRepository(
    ItemsReadRepository,
    interfaces.AbsItemsWriteRepository,
):
    """Repository that performs write operations on items."""

    async def generate_item_uuid(self) -> UUID:
        """Generate new UUID4 for an item."""
        stmt = """
        SELECT 1 FROM items WHERE uuid = :uuid
        UNION
        SELECT 1 FROM orphan_files WHERE item_uuid = :uuid;
        """
        while True:
            uuid = uuid4()
            exists = await self.db.fetch_one(stmt, {'uuid': uuid})

            if not exists:
                return uuid

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
            'uuid': str(item.uuid),
            'parent_uuid': str(item.parent_uuid) if item.parent_uuid else None,
            'name': item.name,
            'is_collection': item.is_collection,
            'content_ext': item.content_ext,
            'preview_ext': item.preview_ext,
            'thumbnail_ext': item.thumbnail_ext,
            'tags': item.tags,
            'permissions': [str(x) for x in item.permissions],
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
        ).returning(
            1
        )

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

    async def update_tags_in_children(
            self,
            item: domain.Item,
    ) -> None:
        """Apply parent tags to every item (and their children too)."""
        total = 0
        start = time.monotonic()

        # TODO - replace with logger call
        print(f'Started updating tags in children of {item.uuid}')

        async def _update_tags(
                _self: ItemsWriteRepository,
                _item: domain.Item,
        ) -> None:
            """Alter tags with themselves.

            Actually we're expecting the database trigger to do all the work.
            Trigger fires after update and computes new tags.
            """
            nonlocal total
            stmt = sqlalchemy.update(
                models.Item
            ).where(
                models.Item.uuid == _item.uuid
            ).values(
                tags=models.Item.tags
            )
            await _self.db.execute(stmt, {'uuid': str(_item.uuid)})
            total += 1

        await self.apply_downwards(
            item=item,
            seen_items=set(),
            skip_items=set(),
            parent_first=True,
            function=_update_tags,
        )

        # TODO - replace with logger call
        delta = time.monotonic() - start
        print('Ended updating tags in '
              f'children of {item.uuid}: {total} operations, {delta:0.3f} sec')

    async def apply_downwards(
            self,
            item: domain.Item,
            seen_items: set[UUID],
            skip_items: set[UUID],
            parent_first: bool,
            function: Callable[['ItemsWriteRepository',
                                domain.Item], Awaitable[None]],
    ) -> None:
        """Apply given function to every descendant item.

        Use cases:
            * We're doing something like delete. Therefore, we must
              delete all children and then their parents.

            * We're doing something like update. Therefore, we must
              update all parents and then their children.
        """
        if item.uuid in seen_items:
            return

        seen_items.add(item.uuid)

        if parent_first and item.uuid not in skip_items:
            await function(self, item)

        children = await self.read_children(item.uuid)

        for child in children:
            await self.apply_downwards(
                item=child,
                seen_items=seen_items,
                skip_items=skip_items,
                parent_first=parent_first,
                function=function,
            )

        if not parent_first and item.uuid not in skip_items:
            await function(self, item)

    async def apply_upwards(
            self,
            item: domain.Item,
            top_first: bool,
            function: Callable[['ItemsWriteRepository',
                                domain.Item], Awaitable[None]],
    ) -> None:
        """Apply given function to every ancestor item.

        Can specify two ways:
            Top -> Middle -> Low -> Current item (top first).
            Current item -> Low -> Middle -> Top (top last).
        """
        ancestors = await self.get_simple_ancestors(item)

        # original order is Top -> Middle -> Low -> Current
        if not top_first:
            ancestors.reverse()

        for ancestor in ancestors:
            await function(self, ancestor)

    async def check_child(
            self,
            possible_parent_uuid: UUID,
            possible_child_uuid: UUID,
    ) -> bool:
        """Return True if given item is actually a child.

        Before checking ensure that UUIDs are not equal. Item is considered
        of being child of itself. This check initially was added to ensure that
        we could not create circular link when setting new parent for the item.
        """
        if possible_parent_uuid == possible_child_uuid:
            return True

        stmt = """
        WITH RECURSIVE nested_items AS (
            SELECT parent_uuid,
                   uuid
            FROM items
            WHERE uuid = :possible_parent_uuid
            UNION ALL
            SELECT i.parent_uuid,
                   i.uuid
            FROM items i
                     INNER JOIN nested_items it2 ON i.parent_uuid = it2.uuid
        )
        SELECT count(*) AS total
        FROM nested_items
        WHERE uuid = :possible_child_uuid;
        """

        values = {
            'possible_parent_uuid': str(possible_parent_uuid),
            'possible_child_uuid': str(possible_child_uuid),
        }

        response = await self.db.fetch_one(stmt, values)

        if response is None:
            return False

        return response['total'] >= 1

    async def update_permissions_in_parents(
            self,
            item: domain.Item,
            new_permissions: domain.NewPermissions,
    ) -> None:
        """Apply new permissions to every parent."""
        total = 0
        start = time.monotonic()

        # TODO - replace with logger call
        print(f'Started updating permissions in parents of {item.uuid}')

        async def _update_permissions(
                _self: ItemsWriteRepository,
                _item: domain.Item,
        ) -> None:
            """Alter permissions."""
            nonlocal total

            _permissions = new_permissions.apply_delta(set(_item.permissions))

            print(f'\tSetting permissions in parents: {total:04d}. '
                  f'{_item.uuid}: '
                  f'{sorted(map(str, _item.permissions))} '
                  f'-> {sorted(map(str, _permissions))}')

            stmt = sqlalchemy.update(
                models.Item
            ).where(
                models.Item.uuid == _item.uuid
            ).values(
                permissions=sorted(str(x) for x in _permissions)
            )

            async with self.transaction():
                await _self.db.execute(stmt)

            total += 1

        await self.apply_upwards(
            item=item,
            top_first=True,
            function=_update_permissions,
        )

        # TODO - replace with logger call
        delta = time.monotonic() - start
        print('Ended updating permissions in '
              f'parents of {item.uuid}: {total} operations, {delta:0.3f} sec')

    async def update_permissions_in_children(
            self,
            item: domain.Item,
            new_permissions: domain.NewPermissions,
    ) -> None:
        """Apply new permissions to every child."""
        total = 0
        start = time.monotonic()

        # TODO - replace with logger call
        print(f'Started updating permissions in children of {item.uuid}')

        async def _update_permissions(
                _self: ItemsWriteRepository,
                _item: domain.Item,
        ) -> None:
            """Alter permissions."""
            nonlocal total

            if new_permissions.override:
                _permissions = new_permissions.permissions_after
            else:
                _permissions = new_permissions.apply_delta(
                    set(_item.permissions)
                )

            print(f'\tSetting permissions in children: {total:04d}. '
                  f'{_item.uuid}: '
                  f'{sorted(map(str, _item.permissions))} '
                  f'-> {sorted(map(str, _permissions))}')

            stmt = sqlalchemy.update(
                models.Item
            ).where(
                models.Item.uuid == _item.uuid
            ).values(
                permissions=sorted(str(x) for x in _permissions)
            )

            async with self.transaction():
                await _self.db.execute(stmt)

            total += 1

        await self.apply_downwards(
            item=item,
            seen_items=set(),
            skip_items=set(),
            parent_first=True,
            function=_update_permissions,
        )

        # TODO - replace with logger call
        delta = time.monotonic() - start
        print('Ended updating permissions in '
              f'children of {item.uuid}: {total} operations, {delta:0.3f} sec')
