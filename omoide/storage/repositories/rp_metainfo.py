# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on metainfo.
"""
import json
from typing import Optional
from uuid import UUID

import sqlalchemy

from omoide import domain
from omoide import utils
from omoide.domain import interfaces
from omoide.storage.database import models


class MetainfoRepository(
    interfaces.AbsMetainfoRepository,
):
    """Repository that perform CRUD operations on metainfo."""

    async def create_empty_metainfo(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> bool:
        """Return True if metainfo was created."""
        stmt = sqlalchemy.insert(
            models.Metainfo
        ).values(
            item_uuid=uuid,
            created_at=utils.now(),
            updated_at=utils.now(),
        )

        await self.db.execute(stmt)

        return True

    async def update_metainfo(
            self,
            user: domain.User,
            metainfo: domain.Metainfo,
    ) -> bool:
        """Update metainfo and return true on success."""
        stmt = sqlalchemy.update(
            models.Metainfo
        ).where(
            models.Metainfo.item_uuid == metainfo.item_uuid
        ).values(
            **metainfo.dict(exclude={'item_uuid', 'created_at'})
        )

        await self.db.execute(stmt)

        return True

    async def read_metainfo(
            self,
            uuid: UUID,
    ) -> Optional[domain.Metainfo]:
        """Return metainfo or None."""
        stmt = sqlalchemy.select(
            models.Metainfo
        ).where(
            models.Metainfo.item_uuid == uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            return None

        return domain.Metainfo(
            item_uuid=response['item_uuid'],

            created_at=response['created_at'],
            updated_at=response['updated_at'],
            deleted_at=response['deleted_at'],
            user_time=response['user_time'],

            width=response['width'],
            height=response['height'],
            duration=response['duration'],
            resolution=response['resolution'],
            size=response['size'],
            media_type=response['media_type'],

            author=response['author'],
            author_url=response['author_url'],
            saved_from_url=response['saved_from_url'],
            description=response['description'],

            extras=json.loads(response['extras']),  # TODO - use ujson here
        )
