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
            'uuid': uuid.uuid4(),
            'parent_uuid': payload.parent_uuid,
            'owner_uuid': user.uuid,
            'name': payload.item_name,
            'is_collection': payload.is_collection,
            'tags': payload.tags,
            'permissions': payload.permissions,
        }

        response = await self.db.execute(query, values)

        return response
