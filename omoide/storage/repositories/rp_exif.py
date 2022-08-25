# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on EXIF.
"""
import json
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import domain
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.storage.database import models


class EXIFRepository(
    repo_interfaces.AbsEXIFRepository,
):
    """Repository that perform CRUD operations on EXIF."""

    async def create_or_update_exif(
            self,
            user: domain.User,
            exif: domain.EXIF,
    ) -> bool:
        """Create EXIF and return True on success."""
        values = {
            'item_uuid': exif.item_uuid,
            'exif': json.dumps(exif.exif, ensure_ascii=False),
        }

        insert = pg_insert(models.EXIF).values(values)
        stmt = insert.on_conflict_do_update(
            constraint='item_uuid',
            set_={'exif': insert.excluded.name}
        )

        response = await self.db.execute(stmt, values)
        return response.rowcount == 1

    async def read_exif(
            self,
            uuid: UUID,
    ) -> Optional[domain.EXIF]:
        """Return EXIF or None."""
        stmt = sa.select(models.EXIF).where(models.EXIF.item_uuid == uuid)
        response = await self.db.fetch_one(stmt)
        return domain.EXIF.from_map(response) if response else None

    async def delete_exif(
            self,
            uuid: UUID,
    ) -> bool:
        """Delete EXIF with given UUID and return True on success."""
        stmt = sa.delete(models.EXIF).where(models.EXIF.item_uuid == uuid)
        response = await self.db.fetch_one(stmt)
        return response.rowcount == 1
