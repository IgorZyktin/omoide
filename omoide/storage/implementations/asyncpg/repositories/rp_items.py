"""Repository that performs operations on items."""

from collections.abc import Collection
from typing import Any
from uuid import UUID
from uuid import uuid4

import sqlalchemy as sa

from omoide import domain
from omoide import exceptions
from omoide import models
from omoide.storage import interfaces as storage_interfaces
from omoide.storage.database import db_models
from omoide.storage.implementations import asyncpg
from omoide.storage.implementations.asyncpg.repositories import queries


class ItemsRepo(storage_interfaces.AbsItemsRepo, asyncpg.AsyncpgStorage):
    """Repository that performs operations on items."""

    async def check_access(
        self,
        user: models.User,
        uuid: UUID,
    ) -> models.AccessStatus:
        """Check access to the Item with given UUID for the given User."""
        query = """
        SELECT owner_uuid,
               exists(SELECT 1
                      FROM public_users pu
                      WHERE pu.user_uuid = owner_uuid) AS is_public,
               (SELECT :user_uuid = ANY (permissions)) AS is_permitted,
               owner_uuid::text = :user_uuid AS is_owner
        FROM items
        WHERE uuid = :uuid;
        """

        values = {
            'user_uuid': str(user.uuid),
            'uuid': str(uuid),
        }
        response = await self.db.fetch_one(query, values)

        if response is None:
            return models.AccessStatus.not_found()

        return models.AccessStatus(
            exists=True,
            is_public=bool(response['is_public']),
            is_permitted=bool(response['is_permitted']),
            is_owner=bool(response['is_owner']),
        )

    async def count_all_children_of(
        self,
        item: domain.Item,
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

        return response['total']

    async def get_root_item(self, user: models.User) -> models.Item:
        """Return root Item for given user."""
        stmt = sa.select(
            db_models.Item
        ).where(
            sa.and_(
                db_models.Item.owner_uuid == user.uuid,
                db_models.Item.parent_uuid == sa.null(),
            )
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'User {user_uuid} has no root item'
            raise exceptions.DoesNotExistError(msg, user_uuid=user.uuid)

        return models.Item(**response)

    async def get_all_root_items(
        self,
        *users: models.User,
    ) -> list[models.Item]:
        """Return list of root items."""
        stmt = sa.select(
            db_models.Item
        ).where(
            db_models.Item.parent_uuid == sa.null()
        )

        if users:
            stmt = stmt.where(
                db_models.Item.owner_uuid.in_(  # noqa
                    tuple(str(user.uuid) for user in users)
                )
            )

        response = await self.db.fetch_all(stmt)
        return [models.Item(**each) for each in response]

    async def read_item(
        self,
        item_uuid: UUID,
    ) -> domain.Item | None:
        """Return item or None."""
        stmt = sa.select(
            db_models.Item
        ).where(
            db_models.Item.uuid == item_uuid
        )

        response = await self.db.fetch_one(stmt)

        return models.Item(**response) if response else None

    async def get_item(self, uuid: UUID) -> models.Item:
        """Return Item."""
        stmt = sa.select(db_models.Item).where(db_models.Item.uuid == uuid)
        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'Item with UUID {uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, uuid=uuid)

        return models.Item(**response)

    async def get_items_anon(
        self,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> list[models.Item]:
        """Return Items."""
        stmt = sa.select(
            db_models.Item
        ).where(
            db_models.Item.owner_uuid.in_(  # noqa
                sa.select(db_models.PublicUsers.user_uuid)
            )
        )

        if parent_uuid is not None:
            stmt = stmt.where(db_models.Item.parent_uuid == parent_uuid)

        if owner_uuid is not None:
            stmt = stmt.where(db_models.Item.owner_uuid == owner_uuid)

        if name is not None:
            stmt = stmt.where(db_models.Item.name == name)

        stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)
        return [models.Item(**row) for row in response]

    async def get_items_known(
        self,
        user: models.User,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> list[models.Item]:
        """Return Items."""
        stmt = sa.select(
            db_models.Item
        ).where(
            sa.or_(
                db_models.Item.permissions.any(str(user.uuid)),
                db_models.Item.owner_uuid == user.uuid,
                db_models.Item.owner_uuid.in_(  # noqa
                    sa.select(db_models.PublicUsers.user_uuid)
                )
            )
        )

        if parent_uuid is not None:
            stmt = stmt.where(db_models.Item.parent_uuid == parent_uuid)

        if owner_uuid is not None:
            stmt = stmt.where(db_models.Item.owner_uuid == owner_uuid)

        if name is not None:
            stmt = stmt.where(db_models.Item.name == name)

        stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)
        return [models.Item(**row) for row in response]

    async def count_items_by_owner(
        self,
        user: models.User,
        collections: bool = False,
    ) -> int:
        """Return total amount of items for given user uuid."""
        stmt = sa.select(
            sa.func.count().label('total_items')
        ).select_from(
            db_models.Item
        ).where(
            db_models.Item.owner_uuid == user.uuid
        )

        if collections:
            stmt = stmt.where(db_models.Item.is_collection)

        response = await self.db.fetch_one(stmt)
        return int(response['total_items'])

    async def get_children(self, item: models.Item) -> list[models.Item]:
        """Return all direct descendants of the given item."""
        stmt = sa.select(
            db_models.Item
        ).where(
            db_models.Item.parent_uuid == item.uuid
        ).order_by(
            db_models.Item.number
        )

        response = await self.db.fetch_all(stmt)
        return [models.Item(**row) for row in response]

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

    async def get_siblings(self, item: models) -> list[models.Item]:
        """Return all siblings for the given item."""
        stmt = sa.select(db_models.Item)

        stmt = stmt.where(
            db_models.Item.parent_uuid == item.parent_uuid
        ).order_by(
            db_models.Item.number
        )

        response = await self.db.fetch_all(stmt)
        return [models.Item(**row) for row in response]

    # TODO - remove this method
    async def get_direct_children_uuids_of(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> list[UUID]:
        """Return all direct items of th given item."""
        stmt = sa.select(
            db_models.Item.uuid
        ).where(
            db_models.Item.parent_uuid == item_uuid,
            sa.or_(
                db_models.Item.permissions.any(str(user.uuid)),
                db_models.Item.owner_uuid == user.uuid,
                db_models.Item.owner_uuid.in_(  # noqa
                    sa.select(db_models.PublicUsers.user_uuid)
                )
            )
        )
        response = await self.db.fetch_all(stmt)
        return list(x['uuid'] for x in response)

    # TODO - remove this method
    async def read_computed_tags(
        self,
        uuid: UUID,
    ) -> list[str]:
        """Return all computed tags for the item."""
        stmt = sa.select(
            db_models.ComputedTags.tags
        ).where(
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
    ) -> domain.Item | None:
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

        return domain.Item(**response) if response else None

    async def get_free_uuid(self) -> UUID:
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

    async def create_item(self, item: models.Item) -> None:
        """Return id for created item."""
        values: dict[str, Any] = {
            'uuid': item.uuid,
            'parent_uuid': item.parent_uuid,
            'owner_uuid': item.owner_uuid,
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

        stmt = sa.insert(
            db_models.Item
        ).values(**values).returning(
            db_models.Item.number,  # TODO - find way to return id
        )

        item_number = await self.db.execute(stmt)
        item.number = item_number

    async def update_item(
        self,
        item: domain.Item,
    ) -> None:
        """Update existing item."""
        stmt = sa.update(
            db_models.Item
        ).values(
            parent_uuid=item.parent_uuid,
            name=item.name,
            is_collection=item.is_collection,
            content_ext=item.content_ext,
            preview_ext=item.preview_ext,
            thumbnail_ext=item.thumbnail_ext,
            tags=item.tags,
            permissions=tuple(str(x) for x in item.permissions),
        ).where(
            db_models.Item.uuid == item.uuid,
        )

        await self.db.execute(stmt)

    async def delete_item(self, item: models.Item) -> None:
        """Delete item."""
        stmt = sa.delete(
            db_models.Item
        ).where(
            db_models.Item.uuid == item.uuid
        )
        await self.db.execute(stmt)

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
                db_models.Item
            ).where(
                db_models.Item.uuid == uuid
            ).values(
                permissions=tuple(str(x) for x in all_permissions),
            )
            await self.db.execute(stmt)

        else:
            if deleted:
                for user in deleted:
                    stmt = sa.update(
                        db_models.Item
                    ).where(
                        db_models.Item.uuid == uuid
                    ).values(
                        permissions=sa.func.array_remove(
                            db_models.Item.permissions,
                            str(user),
                        )
                    )
                    await self.db.execute(stmt)

            if added:
                for user in added:
                    stmt = sa.update(
                        db_models.Item
                    ).where(
                        db_models.Item.uuid == uuid
                    ).values(
                        permissions=sa.func.array_append(
                            db_models.Item.permissions,
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
                db_models.ComputedTags
            ).where(
                db_models.ComputedTags.item_uuid == uuid
            ).values(
                tags=sa.func.array_append(
                    db_models.ComputedTags.tags,
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
                db_models.ComputedTags
            ).where(
                db_models.ComputedTags.item_uuid == uuid
            ).values(
                tags=sa.func.array_remove(
                    db_models.ComputedTags.tags,
                    tag,
                )
            )
            await self.db.execute(stmt)

    async def add_permissions(
        self,
        uuid: UUID,
        permissions: Collection[UUID],
    ) -> None:
        """Add new users to computed permissions of the item."""
        for user_uuid in permissions:
            stmt = sa.update(
                db_models.Item
            ).where(
                db_models.Item.uuid == uuid
            ).values(
                permissions=sa.func.array_append(
                    db_models.Item.permissions,
                    str(user_uuid),
                )
            )
            await self.db.execute(stmt)

    async def delete_permissions(
        self,
        uuid: UUID,
        permissions: Collection[UUID],
    ) -> None:
        """Remove users from computed permissions of the item."""
        for user_uuid in permissions:
            stmt = sa.update(
                db_models.Item
            ).where(
                db_models.Item.uuid == uuid
            ).values(
                permissions=sa.func.array_remove(
                    db_models.Item.permissions,
                    str(user_uuid),
                )
            )
            await self.db.execute(stmt)
