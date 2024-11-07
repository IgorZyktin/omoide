"""Repository that performs operations on items."""

from collections.abc import Collection
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import queries
from omoide.database.interfaces.abs_items_repo import AbsItemsRepo


class ItemsRepo(AbsItemsRepo[AsyncConnection]):
    """Repository that performs operations on items."""

    async def create(self, conn: AsyncConnection, item: models.Item) -> int:
        """Create new item."""
        values: dict[str, Any] = {
            'uuid': item.uuid,
            'parent_id': item.parent_id,
            'parent_uuid': item.parent_uuid,
            'owner_id': item.owner_id,
            'owner_uuid': item.owner_uuid,
            'status': item.status,
            'name': item.name,
            'number': -1,
            'is_collection': item.is_collection,
            'content_ext': item.content_ext,
            'preview_ext': item.preview_ext,
            'thumbnail_ext': item.thumbnail_ext,
            'tags': tuple(item.tags),
            'permissions': tuple(item.permissions),
        }

        if item.id >= 0:
            values['id'] = item.id

        if item.number >= 0:
            values['number'] = item.number

        stmt = sa.insert(db_models.Item).values(**values).returning(db_models.Item.id)

        item_id = (await conn.execute(stmt)).scalar()

        if not item_id:
            return -1

        # NOTE: Initially user id as a number
        update_stmt = (
            sa.update(db_models.Item).where(db_models.Item.id == item_id).values(number=item_id)
        )
        await conn.execute(update_stmt)
        return item_id

    async def get_by_id(self, conn: AsyncConnection, item_id: int) -> models.Item:
        """Return Item with given id."""
        query = sa.select(db_models.Item).where(db_models.Item.id == item_id)
        response = (await conn.execute(query)).first()

        if response is None:
            msg = 'Item with ID {item_id} does not exist'
            raise exceptions.DoesNotExistError(msg, item_id=item_id)

        return models.Item.from_obj(response)

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

        return models.Item.from_obj(response)

    async def get_by_name(self, conn: AsyncConnection, name: str) -> models.Item:
        """Return Item with given name."""
        query = sa.select(db_models.Item).where(db_models.Item.name == name)
        response = (await conn.execute(query)).first()

        if response is None:
            msg = 'Item with name {name!r} does not exist'
            raise exceptions.DoesNotExistError(msg, name=name)

        return models.Item.from_obj(response)

    async def get_children(
        self,
        conn: AsyncConnection,
        item: models.Item,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[models.Item]:
        """Return list of children for given item."""
        query = (
            queries.get_items_with_parent_names()
            .where(db_models.Item.parent_id == item.id)
            .order_by(db_models.Item.number)
        )

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row, extra_keys=['parent_name']) for row in response]

    async def count_children(self, conn: AsyncConnection, item: models.Item) -> int:
        """Count all children of an item with given UUID."""
        query = (
            sa.select(sa.func.count().label('total_items'))
            .select_from(db_models.Item)
            .where(
                db_models.Item.parent_id == item.id,
                db_models.Item.status != models.Status.DELETED,
            )
        )

        response = (await conn.execute(query)).fetchone()
        return int(response.total_items) if response else 0

    async def get_parents(self, conn: AsyncConnection, item: models.Item) -> list[models.Item]:
        """Return list of parents for given item."""
        parents: list[models.Item] = []
        parent_id = item.parent_id

        while parent_id is not None:
            query = sa.select(db_models.Item).where(db_models.Item.id == parent_id)
            raw_parent = (await conn.execute(query)).fetchone()

            if raw_parent is None:
                break

            parent = models.Item.from_obj(raw_parent)
            parents.append(parent)
            parent_id = parent.parent_id

        return list(reversed(parents))

    async def get_siblings(self, conn: AsyncConnection, item: models.Item) -> list[models.Item]:
        """Return list of siblings for given item."""
        query = (
            sa.select(db_models.Item)
            .where(
                db_models.Item.parent_uuid == item.parent_uuid,
                db_models.Item.status != models.Status.DELETED,
            )
            .order_by(db_models.Item.number)
        )

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row) for row in response]

    async def get_family(self, conn: AsyncConnection, item: models.Item) -> list[models.Item]:
        """Return list of all descendants for given item (including item itself)."""
        query = """
        WITH RECURSIVE nested_items AS (
            SELECT id,
                   uuid,
                   parent_id,
                   parent_uuid,
                   owner_id,
                   owner_uuid,
                   status,
                   number,
                   name,
                   is_collection,
                   content_ext,
                   preview_ext,
                   thumbnail_ext,
                   tags,
                   content_ext,
                   permissions
            FROM items
            WHERE id = :id
            UNION ALL
            SELECT i.id,
                   i.uuid,
                   i.parent_id,
                   i.parent_uuid,
                   i.owner_id,
                   i.owner_uuid,
                   i.status,
                   i.number,
                   i.name,
                   i.is_collection,
                   i.content_ext,
                   i.preview_ext,
                   i.thumbnail_ext,
                   i.tags,
                   i.content_ext,
                   i.permissions
            FROM items i
                     INNER JOIN nested_items it2 ON i.parent_id = it2.id
        )
        SELECT * FROM nested_items
        WHERE nested_items.status <> :status;
        """

        values = {'id': item.id, 'status': models.Status.DELETED}
        response = (await conn.execute(sa.text(query), values)).fetchall()
        return [models.Item.from_obj(row) for row in response]

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
            queries.item_is_public(),
            db_models.Item.status != models.Status.DELETED,
        )

        if parent_uuid is not None:
            query = query.where(db_models.Item.parent_uuid == parent_uuid)

        if owner_uuid is not None:
            query = query.where(db_models.Item.owner_uuid == owner_uuid)

        if name is not None:
            query = query.where(db_models.Item.name == name)

        query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row) for row in response]

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
                db_models.Item.permissions.any_() == user.id,
                db_models.Item.owner_id == user.id,
                queries.item_is_public(),
                db_models.Item.status != models.Status.DELETED,
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
        return [models.Item.from_obj(row) for row in response]

    async def is_child(
        self,
        conn: AsyncConnection,
        parent: models.Item,
        child: models.Item,
    ) -> bool:
        """Return True if given item is a child of given parent.

        Item is considered of being child of itself. This check initially was added to ensure that
        we could not create circular links when setting new parent for the item.
        """
        if parent.id == child.id:
            return True

        top_query = (
            sa.select(db_models.Item.parent_id, db_models.Item.id)
            .where(db_models.Item.id == parent.id)
            .cte('nested_items', recursive=True)
        )

        bottom_query = sa.select(db_models.Item.parent_id, db_models.Item.id).join(
            top_query, db_models.Item.parent_id == top_query.c.id
        )

        recursive_query = top_query.union_all(bottom_query)

        total_query = (
            sa.select(sa.func.count().label('total'))
            .select_from(recursive_query)
            .where(recursive_query.c.id == child.id)
        )

        response = (await conn.execute(total_query)).fetchone()
        return bool(response.total >= 1) if response else False

    async def save(self, conn: AsyncConnection, item: models.Item) -> bool:
        """Save the given item."""
        changes = item.get_changes()
        if 'tags' in changes:
            changes['tags'] = tuple(changes['tags'])

        if 'permissions' in changes:
            changes['permissions'] = tuple(changes['permissions'])

        stmt = sa.update(db_models.Item).values(**changes).where(db_models.Item.id == item.id)
        response = await conn.execute(stmt)
        return bool(response.rowcount)

    async def soft_delete(self, conn: AsyncConnection, item: models.Item) -> bool:
        """Mark tem as deleted."""
        item.status = models.Status.DELETED
        return await self.save(conn, item)

    async def delete(self, conn: AsyncConnection, item: models.Item) -> bool:
        """Delete the given item."""
        stmt = sa.delete(db_models.Item).where(db_models.Item.id == item.id)
        response = await conn.execute(stmt)
        return bool(response.rowcount)

    async def read_computed_tags(self, conn: AsyncConnection, item: models.Item) -> list[str]:
        """Return all computed tags for the item."""
        query = sa.select(db_models.ComputedTags.tags).where(
            db_models.ComputedTags.item_id == item.id,
        )
        response = (await conn.execute(query)).fetchone()

        if not response:
            return []
        return list(response.tags)

    async def count_family(self, conn: AsyncConnection, item: models.Item) -> int:
        """Count all descendants for given item (including the item itself)."""
        top_query = (
            sa.select(db_models.Item.parent_id, db_models.Item.status, db_models.Item.id)
            .where(db_models.Item.id == item.id)
            .cte('nested_items', recursive=True)
        )

        bottom_query = sa.select(
            db_models.Item.parent_id, db_models.Item.status, db_models.Item.id
        ).join(top_query, db_models.Item.parent_id == top_query.c.id)

        recursive_query = top_query.union_all(bottom_query)

        total_query = (
            sa.select(sa.func.count().label('total'))
            .select_from(recursive_query)
            .where(recursive_query.c.status != models.Status.DELETED)
        )

        response = (await conn.execute(total_query)).fetchone()
        return int(response.total) if response else 0

    async def get_parent_names(
        self,
        conn: AsyncConnection,
        items: Collection[models.Item],
    ) -> dict[int, str | None]:
        """Get names of parents of the given items."""
        ids = [item.parent_id for item in items if item.parent_id is not None]
        names: dict[int, str | None] = dict.fromkeys(ids)

        subquery = sa.select(
            sa.func.unnest(sa.cast(ids, pg.ARRAY(sa.Integer))).label('id')
        ).subquery('given_id')

        stmt = (
            sa.select(subquery.c.id, db_models.Item.name)
            .join(
                db_models.Item,
                db_models.Item.id == subquery.c.id,
                isouter=True,
            )
            .distinct(subquery.c.id)
        )

        response = (await conn.execute(stmt)).fetchall()

        for row_id, row_name in response:
            names[row_id] = row_name

        return names

    async def get_batch(
        self,
        conn: AsyncConnection,
        only_users: Collection[int],
        only_items: Collection[int],
        batch_size: int,
        last_seen: int | None,
        limit: int | None,
    ) -> list[models.Item]:
        """Iterate on all items."""
        query = sa.select(db_models.Item).where(db_models.Item.status != models.Status.DELETED)

        if last_seen is not None:
            query = query.where(db_models.Item.id > last_seen)

        if only_users:
            query = query.where(db_models.Item.owner_id.in_(only_users))

        if only_items:
            query = query.where(db_models.Item.uuid.in_(only_items))

        query = query.order_by(db_models.Item.id)

        if limit is not None:
            query = query.limit(min(batch_size, limit))
        else:
            query = query.limit(batch_size)

        response = (await conn.execute(query)).fetchall()
        return [models.Item.from_obj(row) for row in response]

    async def cast_uuids(self, conn: AsyncConnection, uuids: Collection[UUID]) -> set[int]:
        """Convert collection of `item_uuid` into set of `item_id`."""
        query = sa.select(db_models.Item.id).where(db_models.Item.uuid.in_(tuple(uuids)))
        response = (await conn.execute(query)).fetchall()
        return {row.id for row in response}

    async def get_map(
        self,
        conn: AsyncConnection,
        ids: Collection[int],
    ) -> dict[int, models.Item | None]:
        """Get map of items."""
        items: dict[int, models.Item | None] = dict.fromkeys(ids)

        query = queries.get_items_with_parent_names().where(db_models.Item.id.in_(tuple(ids)))

        response = (await conn.execute(query)).fetchall()

        for row in response:
            item = models.Item.from_obj(row, extra_keys=['parent_name'])
            items[item.id] = item

        return items

    async def get_duplicates(
        self,
        conn: AsyncConnection,
        user: models.User,
        limit: int,
    ) -> list[models.Duplication]:
        """Return groups of items with same hash."""
        query = (
            sa.select(
                db_models.SignatureMD5.signature,
                sa.func.array_agg(db_models.Item.id).label('ids'),
            )
            .join(
                db_models.SignatureMD5,
                db_models.Item.id == db_models.SignatureMD5.item_id,
            )
            .where(
                db_models.Item.owner_id == user.id,
                db_models.Item.status != models.Status.DELETED,
                ~db_models.Item.is_collection,
            )
            .group_by(db_models.SignatureMD5.signature)
            .having(sa.func.array_length(sa.func.array_agg(db_models.Item.id), 1) > 1)
            .order_by(sa.desc(sa.func.array_length(sa.func.array_agg(db_models.Item.id), 1)))
            .limit(limit)
        )

        response = (await conn.execute(query)).fetchall()

        all_ids: set[int] = set()
        signatures_to_groups: list[tuple[str, list[int]]] = []

        for row in response:
            ids = sorted(row.ids)
            signatures_to_groups.append((row.signature, ids))
            all_ids.update(ids)

        all_items = await self.get_map(conn, all_ids)
        result: list[models.Duplication] = []

        for signature, ids in signatures_to_groups:
            duplication = models.Duplication(signature=signature, examples=[])

            for item_id in ids:
                item = all_items.get(item_id)

                if not item:
                    continue

                parents = await self.get_parents(conn, item)
                duplication.examples.append(models.Example(item, parents))

            result.append(duplication)

        return result
