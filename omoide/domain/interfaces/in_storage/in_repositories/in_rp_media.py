# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on media records.
"""
import abc
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsMediaRepository(in_rp_base.AbsBaseRepository):
    """Repository that perform CRUD operations on media records."""

    @abc.abstractmethod
    async def create_media(
            self,
            user: domain.User,
            media: domain.Media,
    ) -> int:
        """Create Media, return media id."""

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
