# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base


class ItemCRUDRepository(
    base.BaseRepository,
    interfaces.AbsItemCRUDRepository,
):
    """Repository that perform CRUD operations on items and their data."""

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
