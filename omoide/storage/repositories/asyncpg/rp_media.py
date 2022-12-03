# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on media.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide import utils
from omoide.domain import interfaces
from omoide.storage.database import models


class MediaRepository(interfaces.AbsMediaRepository):
    """Repository that perform CRUD operations on media."""

    async def create_media(
            self,
            user: domain.User,
            media: domain.Media,
    ) -> int:
        """Create Media, return media id."""
        stmt = sa.insert(
            models.Media
        ).values(
            owner_uuid=user.uuid,
            item_uuid=media.item_uuid,
            created_at=media.created_at,
            processed_at=media.processed_at,
            content=media.content,
            ext=media.ext,
            target_folder=media.target_folder,
            replication={},
            error='',
            attempts=0,
        ).returning(models.Media.id)
        return await self.db.execute(stmt)

    async def read_media(
            self,
            media_id: int,
    ) -> Optional[domain.Media]:
        """Return Media instance or None."""
        stmt = sa.select(
            models.Media
        ).where(
            models.Media.id == media_id,
        )
        response = await self.db.fetch_one(stmt)
        return domain.Media(**response) if response else None

    async def delete_media(
            self,
            media_id: int,
    ) -> bool:
        """Delete Media with given id, return True on success."""
        stmt = sa.delete(
            models.Media
        ).where(
            models.Media.id == media_id,
        ).returning(1)
        response = await self.db.fetch_one(stmt)
        return response is not None

    async def copy_media(
            self,
            owner_uuid: UUID,
            source_uuid: UUID,
            target_uuid: UUID,
            ext: str,
            target_folder: str,
    ) -> bool:
        """Save intention to copy data between items."""
        query = sa.insert(
            models.ManualCopy
        ).values(
            created_at=utils.now(),
            processed_at=None,
            status='init',
            error='',
            owner_uuid=str(owner_uuid),
            source_uuid=str(source_uuid),
            target_uuid=str(target_uuid),
            ext=ext,
            target_folder=target_folder,
        )
        await self.db.execute(query)
        return True
