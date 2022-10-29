# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on media records.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsMediaRepository(in_rp_base.AbsBaseRepository):
    """Repository that perform CRUD operations on media records."""

    @abc.abstractmethod
    async def create_or_update_media(
            self,
            user: domain.User,
            media: domain.Media,
    ) -> bool:
        """Create/update Media, return True if media was created."""

    @abc.abstractmethod
    async def read_media(
            self,
            uuid: UUID,
            media_type: str,
    ) -> Optional[domain.Media]:
        """Return Media instance or None."""

    @abc.abstractmethod
    async def delete_media(
            self,
            uuid: UUID,
            media_type: str,
    ) -> bool:
        """Delete Media with given UUID, return True on success."""

    @abc.abstractmethod
    async def create_filesystem_operation(
            self,
            source_uuid: UUID,
            target_uuid: UUID,
            operation: str,
            extras: dict[str, str | int | bool | None],
    ) -> bool:
        """Save intention to init operation on the filesystem."""
