# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
from typing import Optional
from uuid import UUID, uuid4

from omoide import domain
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.storage import repositories as repo_implementations


class ItemsRepository(
    repo_implementations.BaseRepository,
    repo_interfaces.AbsItemsRepository,
):
    """Repository that perform CRUD operations on items and their data."""

    async def generate_uuid(self) -> UUID:
        """Generate new UUID4 for an item."""
        stmt = """
        SELECT 1 FROM items WHERE uuid = :uuid;
        """
        while True:
            uuid = uuid4()
            exists = await self.db.fetch_one(stmt, {'uuid': uuid})

            if not exists:
                return uuid

    async def create_item(
            self,
            user: domain.User,
            payload: domain.CreateItemIn,
    ) -> UUID:
        """Create item and return UUID."""
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
        WHERE uuid = :uuid;
        """

        response = await self.db.fetch_one(stmt, {'uuid': uuid})
        return domain.Item.from_map(response) if response else None

    async def update_item(
            self,
            payload: domain.UpdateItemIn,
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
            'uuid': payload.uuid,
            'parent_uuid': payload.parent_uuid,
            'name': payload.name,
            'is_collection': payload.is_collection,
            'content_ext': payload.content_ext,
            'preview_ext': payload.preview_ext,
            'thumbnail_ext': payload.thumbnail_ext,
            'tags': payload.tags,
            'permissions': payload.permissions,
        }

        return await self.db.execute(stmt, values)

    async def delete_item(
            self,
            uuid: UUID,
    ) -> None:
        """Delete item with given UUID."""
        stmt = """
        DELETE FROM items WHERE uuid = :uuid;
        """
        await self.db.execute(stmt, {'uuid': uuid})
