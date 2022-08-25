# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on EXIF records.
"""
import abc
from typing import Optional, Any
from uuid import UUID

from omoide import domain


class AbsEXIFRepository(abc.ABC):
    """Repository that perform CRUD operations on EXIF records."""

    def __init__(self, db) -> None:  # TODO - move to base class
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:  # TODO - move to base class
        """Start transaction."""
        return self.db.transaction()

    @abc.abstractmethod
    async def create_or_update_exif(
            self,
            user: domain.User,
            exif: domain.EXIF,
    ) -> bool:
        """Return True if EXIF was created."""

    @abc.abstractmethod
    async def read_exif(
            self,
            uuid: UUID,
    ) -> Optional[domain.EXIF]:
        """Return EXIF or None."""

    @abc.abstractmethod
    async def delete_exif(
            self,
            uuid: UUID,
    ) -> bool:
        """Delete EXIF with given UUID."""
