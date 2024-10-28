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

    async def get_by_name(self, conn: AsyncConnection, name: str,) -> models.Item:
        """Return Item with given name."""
        query = sa.select(db_models.Item).where(db_models.Item.name == name)
        response = (await conn.execute(query)).first()

        if response is None:
            msg = 'Item with name {name!r} does not exist'
            raise exceptions.DoesNotExistError(msg, name=name)

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

    async def get_items_anon(
        self,
        conn: AsyncConnection,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> list[models.Item]:
        """Return Items."""
        query = sa.select(db_models.Item).where(
            db_models.Item.owner_uuid.in_(  # noqa
                sa.select(db_models.PublicUsers.user_uuid)
            )
        )

        if parent_uuid is not None:
            query = query.where(db_models.Item.parent_uuid == parent_uuid)

        if owner_uuid is not None:
            query = query.where(db_models.Item.owner_uuid == owner_uuid)

        if name is not None:
            query = query.where(db_models.Item.name == name)

        query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [db_models.Item.cast(row) for row in response]

    async def get_items_known(
        self,
        conn: AsyncConnection,
        user: models.User,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> list[models.Item]:
        """Return Items."""
        query = sa.select(db_models.Item).where(
            sa.or_(
                db_models.Item.permissions.any(str(user.uuid)),
                db_models.Item.owner_uuid == user.uuid,
                db_models.Item.owner_uuid.in_(sa.select(db_models.PublicUsers.user_uuid)),
            )
        )

        if parent_uuid is not None:
            query = query.where(db_models.Item.parent_uuid == parent_uuid)

        if owner_uuid is not None:
            query = query.where(db_models.Item.owner_uuid == owner_uuid)

        if name is not None:
            query = query.where(db_models.Item.name == name)

        query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [db_models.Item.cast(row) for row in response]

    async def check_child(
        self,
        conn: AsyncConnection,
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

        query = """
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

        response = (await conn.execute(sa.text(query), values)).fetchone()

        if response is None:
            return False

        return bool(response.total >= 1)

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
