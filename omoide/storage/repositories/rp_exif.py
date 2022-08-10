# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on EXIF.
"""
import json
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.storage import repositories as repo_implementations
from omoide.storage.database import models


class EXIFRepository(
    repo_implementations.BaseRepository,
    repo_interfaces.AbsEXIFRepository,
):
    """Repository that perform CRUD operations on EXIF."""

    async def create_or_update_exif(
            self,
            user: domain.User,
            media: domain.EXIF,
    ) -> bool:
        """Create item and return UUID."""
        stmt = """
        INSERT INTO exif (
            item_uuid,
            exif
        ) VALUES (
            :item_uuid,
            :exif
        ) ON CONFLICT (item_uuid) DO UPDATE SET
            exif = excluded.exif;
        """

        values = {
            'item_uuid': media.item_uuid,
            'exif': json.dumps(media.exif, ensure_ascii=False),
        }

        await self.db.execute(stmt, values)
        return False  # FIXME - return something

    async def read_exif(
            self,
            uuid: UUID,
    ) -> Optional[domain.EXIF]:
        """Return media or None."""
        stmt = sa.select(models.EXIF).where(models.EXIF.item_uuid == uuid)
        response = await self.db.fetch_one(stmt)
        return domain.Media.from_map(response) if response else None

    async def delete_exif(
            self,
            uuid: UUID,
    ) -> bool:
        """Delete media for the item with given UUID."""
        stmt = sa.delete(models.EXIF).where(models.EXIF.item_uuid == uuid)
        response = await self.db.fetch_one(stmt)
        return response.rowcount == 1
