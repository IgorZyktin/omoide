"""Repository that performs operations on items."""

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_items_repo import AbsItemsRepo


class ItemsRepo(AbsItemsRepo[AsyncConnection]):
    """Repository that performs operations on items."""

    async def create(self, conn: AsyncConnection, item: models.Item) -> int:
        """Create new item."""
        values: dict[str, Any] = {
            'uuid': item.uuid,
            'parent_uuid': item.parent_uuid,
            'owner_uuid': item.owner_uuid,
            'status': item.status,
            'name': item.name,
            'number': item.number,
            'is_collection': item.is_collection,
            'content_ext': item.content_ext,
            'preview_ext': item.preview_ext,
            'thumbnail_ext': item.thumbnail_ext,
            'tags': tuple(item.tags),
            'permissions': tuple(str(x) for x in item.permissions),
        }

        if item.id >= 0:
            values['id'] = item.id

        stmt = (
            sa.insert(db_models.Item)
            .values(**values)
            .returning(
                db_models.Item.id,
            )
        )

        response = await conn.execute(stmt)
        item_id = int(response.scalar() or -1)
        item.id = item_id
        return item_id

    async def get_by_id(self, conn: AsyncConnection, item_id: int) -> models.Item:
        """Return Item with given id."""
        query = sa.select(db_models.Item).where(db_models.Item.id == item_id)
        response = (await conn.execute(query)).first()

        if response is None:
            msg = 'Item with ID {item_id} does not exist'
            raise exceptions.DoesNotExistError(msg, item_id=item_id)

        return db_models.Item.cast(response)

    async def get_by_uuid(
        self,
        conn: AsyncConnection,
        uuid: UUID,
    ) -> models.Item:
        """Return User with given UUID."""
        query = sa.select(db_models.Item).where(db_models.Item.uuid == uuid)
        response = (await conn.execute(query)).first()

        if response is None:
            msg = 'Item with UUID {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=uuid)

        return db_models.Item.cast(response)

    async def get_children(self, conn: AsyncConnection, item: models.Item) -> list[models.Item]:
        """Return list of children for given item."""
        query = (
            sa.select(db_models.Item)
            .where(db_models.Item.parent_uuid == item.uuid)
            .order_by(db_models.Item.id)
        )
        response = (await conn.execute(query)).fetchall()
        return [db_models.Item.cast(row) for row in response]

    async def count_children(self, conn: AsyncConnection, item: models.Item) -> int:
        """Count all children of an item with given UUID."""
        query = (
            sa.select(sa.func.count().label('total_items'))
            .select_from(db_models.Item)
            .where(db_models.Item.parent_uuid == item.uuid)
        )

        response = (await conn.execute(query)).fetchone()
        return int(response.total_items)

    async def get_parents(self, conn: AsyncConnection, item: models.Item) -> list[models.Item]:
        """Return list of parents for given item."""
        parents: list[models.Item] = []
        parent_uuid = item.parent_uuid

        while parent_uuid:
            query = sa.select(db_models.Item).where(db_models.Item.uuid == parent_uuid)
            raw_parent = (await conn.execute(query)).fetchone()

            if raw_parent is None:
                break

            parent = db_models.Item.cast(raw_parent)
            parents.append(parent)
            parent_uuid = parent.parent_uuid

        return list(reversed(parents))

    async def get_siblings(self, conn: AsyncConnection, item: models.Item) -> list[models.Item]:
        """Return list of siblings for given item."""
        query = (
            sa.select(db_models.Item)
            .where(db_models.Item.parent_uuid == item.parent_uuid)
            .order_by(db_models.Item.number)
        )

        response = (await conn.execute(query)).fetchall()
        return [db_models.Item.cast(row) for row in response]

    async def save(self, conn: AsyncConnection, item: models.Item) -> bool:
        """Save the given item."""
        stmt = (
            sa.update(db_models.Item)
            .values(
                parent_uuid=item.parent_uuid,
                name=item.name,
                status=item.status.value,
                number=item.number,
                is_collection=item.is_collection,
                content_ext=item.content_ext,
                preview_ext=item.preview_ext,
                thumbnail_ext=item.thumbnail_ext,
                tags=tuple(item.tags),
                permissions=tuple(str(x) for x in item.permissions),
            )
            .where(db_models.Item.id == item.id)
        )
        response = await conn.execute(stmt)
        return bool(response.rowcount)

    async def delete(self, conn: AsyncConnection, item: models.Item) -> bool:
        """Delete the given item."""
        stmt = sa.delete(db_models.Item).where(db_models.Item.id == item.id)
        response = await conn.execute(stmt)
        return bool(response.rowcount)
