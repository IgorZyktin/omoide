# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on media.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import domain
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.storage.database import models


class MediaRepository(
    repo_interfaces.AbsMediaRepository,
):
    """Repository that perform CRUD operations on media."""

    async def create_or_update_media(
            self,
            user: domain.User,
            media: domain.Media,
    ) -> bool:
        """Create item and return UUID."""
        values = {
            'item_uuid': media.item_uuid,
            'created_at': media.created_at,
            'processed_at': media.processed_at,
            'status': media.status,
            'content': media.content,
            'ext': media.ext,
            'media_type': media.media_type,
        }

        insert = pg_insert(
            models.Media
        ).values(
            values
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[
                models.Media.item_uuid,
                models.Media.media_type,
            ],
            set_={
                'created_at': insert.excluded.created_at,
                'processed_at': insert.excluded.processed_at,
                'status': insert.excluded.status,
                'ext': insert.excluded.ext,
                'media_type': insert.excluded.media_type,
            }
        )

        await self.db.execute(stmt, values)

        return True

    async def read_media(
            self,
            uuid: UUID,
            media_type: str,
    ) -> Optional[domain.Media]:
        """Return media or None."""
        stmt = sa.select(
            models.Media
        ).where(
            models.Media.item_uuid == uuid,
            models.Media.media_type == media_type,
            sa.literal(media_type).label('media_type'),
        )

        response = await self.db.fetch_one(stmt)

        return domain.Media(**response) if response else None

    async def delete_media(
            self,
            uuid: UUID,
            media_type: str,
    ) -> bool:
        """Delete media for the item with given UUID."""
        stmt = sa.delete(
            models.Media
        ).where(
            models.Media.item_uuid == uuid,
            models.Media.media_type == media_type,
        ).returning(1)

        response = await self.db.fetch_one(stmt)

        return response is not None
