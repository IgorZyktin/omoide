# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on EXIF records.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsEXIFRepository(in_rp_base.AbsBaseRepository):
    """Repository that perform CRUD operations on EXIF records."""

    @abc.abstractmethod
    async def create_or_update_exif(
            self,
            user: domain.User,
            exif: domain.EXIF,
    ) -> bool:
        """Create/update EXIF, return True if EXIF was created."""

    @abc.abstractmethod
    async def read_exif(
            self,
            uuid: UUID,
    ) -> Optional[domain.EXIF]:
        """Return EXIF instance or None."""

    @abc.abstractmethod
    async def delete_exif(
            self,
            uuid: UUID,
    ) -> bool:
        """Delete EXIF with given UUID."""
