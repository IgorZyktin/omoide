# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on media.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
import ujson

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
            item_uuid=media.item_uuid,
            created_at=media.created_at,
            processed_at=media.processed_at,
            content=media.content,
            ext=media.ext,
            media_type=media.media_type,
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

    async def create_filesystem_operation(
            self,
            source_uuid: UUID,
            target_uuid: UUID,
            operation: str,
            extras: dict[str, str | int | bool | None],
    ) -> bool:
        """Save intention to init operation on the filesystem."""
        query = sa.insert(
            models.FilesystemOperation
        ).values(
            created_at=utils.now(),
            processed_at=None,
            status='init',
            error='',
            source_uuid=str(source_uuid),
            target_uuid=str(target_uuid),
            operation=operation,
            extras=ujson.dumps(extras, ensure_ascii=False),
        )
        await self.db.execute(query)
        return True
