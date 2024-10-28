"""Repository that performs operations on items."""

from collections.abc import Collection
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import queries
from omoide.database.interfaces.abs_items_repo import AbsItemsRepo


class ItemsRepo(AbsItemsRepo):
    """Repository that performs operations on items."""

    async def count_all_children_of(
        self,
        item: models.Item,
    ) -> int:
        """Count dependant items."""
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

        response = await self.db.fetch_one(stmt, {'uuid': item.uuid})

        if response is None:
            return 0

        return int(response['total'])

    async def read_item(
        self,
        item_uuid: UUID,
    ) -> models.Item | None:
        """Return item or None."""
        stmt = sa.select(db_models.Item).where(db_models.Item.uuid == item_uuid)

        response = await self.db.fetch_one(stmt)

        return models.Item(**response) if response else None

    async def get_item(self, uuid: UUID) -> models.Item:
        """Return Item."""
        stmt = sa.select(db_models.Item).where(db_models.Item.uuid == uuid)
        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'Item with UUID {uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, uuid=uuid)

        raw_item = dict(response)
        permissions = raw_item.pop('permissions', [])
        return models.Item(
            **raw_item,
            permissions={UUID(x) for x in permissions},
        )

    async def count_items_by_owner(
        self,
        user: models.User,
        collections: bool = False,
    ) -> int:
        """Return total amount of items for given user uuid."""
        stmt = (
            sa.select(sa.func.count().label('total_items'))
            .select_from(db_models.Item)
            .where(db_models.Item.owner_uuid == user.uuid)
        )

        if collections:
            stmt = stmt.where(db_models.Item.is_collection)

        response = await self.db.fetch_one(stmt)
        return int(response['total_items'])

    async def get_parents(self, item: models.Item) -> list[models.Item]:
        """Return lineage of all parents for the given item."""
        stmt = """
        WITH RECURSIVE parents AS (
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
           FROM items
           WHERE uuid = :uuid
           UNION
           SELECT i.id,
                  i.uuid,
                  i.parent_uuid,
                  i.owner_uuid,
                  i.number,
                  i.name,
                  i.is_collection,
                  i.content_ext,
                  i.preview_ext,
                  i.thumbnail_ext,
                  i.tags,
                  i.permissions
            FROM items i
                     INNER JOIN parents ON i.uuid = parents.parent_uuid
        )
        SELECT * FROM parents WHERE parents.uuid <> :uuid;
        """

        values = {'uuid': str(item.uuid)}

        response = await self.db.fetch_all(stmt, values)
        return [models.Item(**row) for row in reversed(response)]

    # TODO - remove this method
    async def read_computed_tags(
        self,
        uuid: UUID,
    ) -> list[str]:
        """Return all computed tags for the item."""
        stmt = sa.select(db_models.ComputedTags.tags).where(
            db_models.ComputedTags.item_uuid == uuid,
        )
        response = await self.db.execute(stmt)

        if response:
            return list(response)
        return []

    async def read_item_by_name(
        self,
        user: models.User,
        name: str,
    ) -> models.Item | None:
        """Return corresponding item."""
        stmt = sa.select(db_models.Item)

        if user.is_anon:
            stmt = stmt.where(
                sa.and_(
                    db_models.Item.name == name,
                )
            )
        else:
            stmt = stmt.where(
                sa.and_(
                    db_models.Item.owner_uuid == user.uuid,
                    db_models.Item.name == name,
                )
            )

        stmt = queries.ensure_user_has_permissions(user, stmt)
        response = await self.db.fetch_one(stmt)

        return models.Item(**response) if response else None

    async def create_item(self, item: models.Item) -> None:
        """Return id for created item."""
        values: dict[str, Any] = {
            'uuid': item.uuid,
            'parent_uuid': item.parent_uuid,
            'owner_uuid': item.owner_uuid,
            # TODO - currently all items are available from the start
            'status': models.Status.AVAILABLE.value,
            'name': item.name,
            'is_collection': item.is_collection,
            'content_ext': item.content_ext,
            'preview_ext': item.preview_ext,
            'thumbnail_ext': item.thumbnail_ext,
            'tags': tuple(item.tags),
            'permissions': tuple(str(x) for x in item.permissions),
        }

        if item.number > 0:
            values['number'] = item.number

        stmt = (
            sa.insert(db_models.Item)
            .values(**values)
            .returning(
                db_models.Item.number,
            )
        )

        item_number = await self.db.execute(stmt)
        item.number = item_number

    async def update_item(
        self,
        item: models.Item,
    ) -> None:
        """Update existing item."""
        stmt = (
            sa.update(db_models.Item)
            .values(
                parent_uuid=item.parent_uuid,
                name=item.name,
                is_collection=item.is_collection,
                content_ext=item.content_ext,
                preview_ext=item.preview_ext,
                thumbnail_ext=item.thumbnail_ext,
                tags=tuple(item.tags),
                permissions=tuple(str(x) for x in item.permissions),
            )
            .where(
                db_models.Item.uuid == item.uuid,
            )
        )

        await self.db.execute(stmt)

    async def delete_item(self, item: models.Item) -> None:
        """Delete item."""
        stmt = sa.delete(db_models.Item).where(db_models.Item.uuid == item.uuid)
        await self.db.execute(stmt)


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
            stmt = (
                sa.update(db_models.Item)
                .where(db_models.Item.uuid == uuid)
                .values(
                    permissions=tuple(str(x) for x in all_permissions),
                )
            )
            await self.db.execute(stmt)

        else:
            if deleted:
                for user in deleted:
                    stmt = (
                        sa.update(db_models.Item)
                        .where(db_models.Item.uuid == uuid)
                        .values(
                            permissions=sa.func.array_remove(
                                db_models.Item.permissions,
                                str(user),
                            )
                        )
                    )
                    await self.db.execute(stmt)

            if added:
                for user in added:
                    stmt = (
                        sa.update(db_models.Item)
                        .where(db_models.Item.uuid == uuid)
                        .values(
                            permissions=sa.func.array_append(
                                db_models.Item.permissions,
                                str(user),
                            )
                        )
                    )
                    await self.db.execute(stmt)
