# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
import uuid

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base


class ItemCRUDRepository(
    base.BaseRepository,
    interfaces.AbsItemCRUDRepository,
):
    """Repository that perform CRUD operations on items and their data."""

    async def create_root_item(
            self,
            user: domain.User,
            payload: domain.CreateItemPayload,
    ) -> str:
        """Create item without parent."""
        query = """
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
            NULL,
            :owner_uuid,
            max(number) + 1 as new_number,
            :name,
            :is_collection,
            '',
            '',
            '',
            :tags,
            :permissions
        FROM items
        RETURNING uuid;
        """

        values = {
            'uuid': uuid.uuid4(),
            'owner_uuid': user.uuid,
            'name': payload.item_name,
            'is_collection': payload.is_collection,
            'tags': payload.tags,
            'permissions': payload.permissions,
        }

        response = await self.db.execute(query, values)

        return response

    async def create_dependant_item(
            self,
            user: domain.User,
            payload: domain.CreateItemPayload,
    ) -> domain.Item:
        """Create item with parent."""
        query = """
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
            '',
            '',
            '',
            :tags,
            :permissions
        FROM items
        RETURNING uuid;
        """

        values = {
            'uuid': payload.uuid,
            'parent_uuid': payload.parent_uuid,
            'owner_uuid': user.uuid,
            'name': payload.item_name,
            'is_collection': payload.is_collection,
            'tags': payload.tags,
            'permissions': payload.permissions,
        }

        response = await self.db.execute(query, values)

        return response

    async def save_raw_media(
            self,
            payload: domain.RawMedia,
    ) -> bool:
        """Save given content to the DB."""
        query = """
        INSERT INTO raw_media (
            item_uuid,
            created_at,
            processed_at,
            status,
            filename,
            content,
            features
        )
        VALUES (
            :item_uuid,
            :created_at,
            :processed_at,
            :status,
            :filename,
            :content,
            :features
        );
        """

        values = {
            'item_uuid': payload.uuid,
            'created_at': payload.created_at,
            'processed_at': payload.processed_at,
            'status': payload.status,
            'filename': payload.filename,
            'content': payload.content,
            'features': payload.features,
        }

        await self.db.execute(query, values)
        return True
