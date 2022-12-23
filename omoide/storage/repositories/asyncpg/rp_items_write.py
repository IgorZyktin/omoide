# -*- coding: utf-8 -*-
"""Repository that performs write operations on items.
"""
import datetime
import time
from typing import Awaitable
from typing import Callable
from typing import Collection
from uuid import UUID
from uuid import uuid4

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.infra import custom_logging
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg.rp_items_read import \
    ItemsReadRepository

LOG = custom_logging.get_logger(__name__)


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
            item: domain.Item,
    ) -> UUID:
        """Create item and return UUID."""
        if item.parent_uuid is None:
            parent_uuid = None
        else:
            parent_uuid = str(item.parent_uuid)

        def get_number():
            if item.number == -1:
                return sa.func.max(models.Item.number) + 1
            return item.number

        select_stmt = sa.select(
            sa.literal(str(item.uuid)).label('uuid'),
            sa.literal(parent_uuid).label('parent_uuid'),
            sa.literal(str(user.uuid)).label('owner_uuid'),
            (get_number()).label('number'),
            sa.literal(item.name).label('name'),
            sa.literal(item.is_collection).label('is_collection'),
            sa.literal(item.content_ext).label('content_ext'),
            sa.literal(item.preview_ext).label('preview_ext'),
            sa.literal(item.thumbnail_ext).label('thumbnail_ext'),
            sa.literal(item.tags).label('tags'),
            sa.literal([str(x) for x in item.permissions]).label('permissions')
        )

        stmt = sa.insert(
            models.Item
        ).from_select(
            [*select_stmt.columns],
            select_stmt
        ).returning(models.Item.uuid)

        return await self.db.execute(stmt)

    async def update_item(
            self,
            item: domain.Item,
    ) -> UUID:
        """Update existing item."""
        stmt = sa.update(
            models.Item
        ).values(
            parent_uuid=item.parent_uuid,
            name=item.name,
            is_collection=item.is_collection,
            content_ext=item.content_ext,
            preview_ext=item.preview_ext,
            thumbnail_ext=item.thumbnail_ext,
            tags=item.tags,
            permissions=[str(x) for x in item.permissions],
        ).where(
            models.Item.uuid == item.uuid,
        )

        return await self.db.execute(stmt)

    async def mark_files_as_orphans(
            self,
            item: domain.Item,
            moment: datetime.datetime,
    ) -> None:
        """Mark corresponding files as useless."""
        if item.content_ext is not None:
            stmt = sa.insert(
                models.OrphanFiles
            ).values(
                media_type='content',
                owner_uuid=item.owner_uuid,
                item_uuid=item.uuid,
                ext=item.content_ext,
                moment=moment,
            )
            await self.db.execute(stmt)

        if item.preview_ext is not None:
            stmt = sa.insert(
                models.OrphanFiles
            ).values(
                media_type='preview',
                owner_uuid=item.owner_uuid,
                item_uuid=item.uuid,
                ext=item.preview_ext,
                moment=moment,
            )
            await self.db.execute(stmt)

        if item.thumbnail_ext is not None:
            stmt = sa.insert(
                models.OrphanFiles
            ).values(
                media_type='thumbnail',
                owner_uuid=item.owner_uuid,
                item_uuid=item.uuid,
                ext=item.thumbnail_ext,
                moment=moment,
            )
            await self.db.execute(stmt)

    async def delete_item(
            self,
            item: domain.Item,
    ) -> bool:
        """Delete item with given UUID."""
        stmt = sa.delete(
            models.Item
        ).where(
            models.Item.uuid == item.uuid,
        ).returning(1)

        response = await self.db.fetch_one(stmt)
        return response is not None

    async def apply_downwards(
            self,
            user: domain.User,
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

        children = await self.read_children_of(
            user, item, ignore_collections=False)

        for child in children:
            await self.apply_downwards(
                user=user,
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
            user: domain.User,
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
        ancestors = await self.get_simple_ancestors(user, item)

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

    async def update_permissions(
            self,
            uuid: UUID,
            override: bool,
            added: Collection[UUID],
            deleted: Collection[UUID],
            all_permissions: Collection[UUID],
    ) -> None:
        """Apply new permissions for given item UUID."""
        if override:
            stmt = sa.update(
                models.Item
            ).where(
                models.Item.uuid == uuid
            ).values(
                permissions=tuple(str(x) for x in all_permissions),
            )
            await self.db.execute(stmt)

        else:
            if deleted:
                for user in deleted:
                    stmt = sa.update(
                        models.Item
                    ).where(
                        models.Item.uuid == uuid
                    ).values(
                        permissions=sa.func.array_remove(
                            models.Item.permissions,
                            str(user),
                        )
                    )
                    await self.db.execute(stmt)

            if added:
                for user in added:
                    stmt = sa.update(
                        models.Item
                    ).where(
                        models.Item.uuid == uuid
                    ).values(
                        permissions=sa.func.array_append(
                            models.Item.permissions,
                            str(user),
                        )
                    )
                    await self.db.execute(stmt)

    async def add_tags(
            self,
            uuid: UUID,
            tags: Collection[str],
    ) -> None:
        """Add new tags to computed tags of the item."""
        for tag in tags:
            stmt = sa.update(
                models.ComputedTags
            ).where(
                models.ComputedTags.item_uuid == uuid
            ).values(
                tags=sa.func.array_append(
                    models.ComputedTags.tags,
                    tag,
                )
            )
            await self.db.execute(stmt)

    async def delete_tags(
            self,
            uuid: UUID,
            tags: Collection[str],
    ) -> None:
        """Remove tags from computed tags of the item."""
        for tag in tags:
            stmt = sa.update(
                models.ComputedTags
            ).where(
                models.ComputedTags.item_uuid == uuid
            ).values(
                tags=sa.func.array_remove(
                    models.ComputedTags.tags,
                    tag,
                )
            )
            await self.db.execute(stmt)
