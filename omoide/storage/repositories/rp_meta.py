# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on metas.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
import ujson

from omoide import domain
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.storage import repositories as repo_implementations
from omoide.storage.database import models


class MetaRepository(
    repo_implementations.BaseRepository,
    repo_interfaces.AbsMetaRepository,
):
    """Repository that perform CRUD operations on meta."""

    async def create_or_update_meta(
            self,
            user: domain.User,
            meta: domain.Meta,
    ) -> bool:
        """Create meta and return UUID."""
        stmt = """
        INSERT INTO meta (
            item_uuid,
            data
        ) VALUES (
            :item_uuid,
            :data
        ) ON CONFLICT (item_uuid) DO UPDATE SET
            data = excluded.data;
        """

        for key, value in meta.meta.items():
            if isinstance(value, datetime):
                meta.meta[key] = str(value)

        values = {
            'item_uuid': meta.item_uuid,
            'data': ujson.dumps(meta.meta, ensure_ascii=False),
        }

        await self.db.execute(stmt, values)
        return False  # FIXME - return something

    async def read_meta(
            self,
            uuid: UUID,
    ) -> Optional[domain.Meta]:
        """Return meta or None."""
        stmt = sa.select(models.Meta).where(models.Meta.item_uuid == uuid)
        response = await self.db.fetch_one(stmt)
        return domain.Meta.from_map(response) if response else None
