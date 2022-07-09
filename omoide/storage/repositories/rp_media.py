# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on media.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.storage import repositories as repo_implementations
from omoide.storage.database import models


class MediaRepository(
    repo_implementations.BaseRepository,
    repo_interfaces.AbsMediaRepository,
):
    """Repository that perform CRUD operations on media."""

    async def create_or_update_media(
            self,
            user: domain.User,
            media: domain.Media,
    ) -> bool:
        """Create item and return UUID."""
        stmt = """
        INSERT INTO media (
            item_uuid,
            created_at,
            processed_at,
            status,
            content,
            ext,
            media_type
        ) VALUES (
            :item_uuid,
            :created_at,
            :processed_at,
            :status,
            :content,
            :ext,
            :media_type
        ) ON CONFLICT (item_uuid, media_type) DO UPDATE SET
            created_at = excluded.created_at,
            processed_at = excluded.processed_at,
            status = excluded.status,
            ext = excluded.ext,
            media_type = excluded.media_type;
        """

        values = {
            'item_uuid': media.item_uuid,
            'created_at': media.created_at,
            'processed_at': media.processed_at,
            'status': media.status,
            'content': media.content,
            'ext': media.ext,
            'media_type': media.media_type,
        }

        await self.db.execute(stmt, values)
        return False  # FIXME - return something

    async def read_media(
            self,
            uuid: UUID,
            media_type: str,
    ) -> Optional[domain.Media]:
        """Return media or None."""
        stmt = sa.select(models.Media).where(
            models.Media.item_uuid == uuid,
            models.Media.media_type == media_type,
            sa.literal(media_type).label('media_type'),
        )
        response = await self.db.fetch_one(stmt)
        return domain.Media.from_map(response) if response else None

    async def delete_media(
            self,
            uuid: UUID,
            media_type: str,
    ) -> bool:
        """Delete media for the item with given UUID."""
        stmt = sa.delete(models.Media).where(
            models.Media.item_uuid == uuid,
            models.Media.media_type == media_type,
        )
        response = await self.db.fetch_one(stmt)
        return response.rowcount == 1
