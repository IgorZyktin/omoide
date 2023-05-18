# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on media records.
"""
import abc
from typing import Optional
from uuid import UUID

import omoide.domain.models
from omoide import domain
from omoide.domain import models
from omoide.domain.interfaces.in_storage import in_rp_base


class AbsMediaRepository(in_rp_base.AbsBaseRepository):
    """Repository that perform CRUD operations on media records."""

    @abc.abstractmethod
    async def create_media(
            self,
            user: omoide.domain.models.User,
            media: models.Media,
    ) -> int:
        """Create Media, return media id."""

    @abc.abstractmethod
    async def read_media(
            self,
            media_id: int,
    ) -> Optional[models.Media]:
        """Return Media instance or None."""

    @abc.abstractmethod
    async def delete_media(
            self,
            media_id: int,
    ) -> bool:
        """Delete Media with given id, return True on success."""

    @abc.abstractmethod
    async def copy_media(
            self,
            owner_uuid: UUID,
            source_uuid: UUID,
            target_uuid: UUID,
            ext: str,
            target_folder: str,
    ) -> bool:
        """Save intention to copy data between items."""
