# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on metainfo records.
"""
import abc
from typing import Any
from typing import Optional
from uuid import UUID

from omoide import domain


class AbsMetainfoRepository(abc.ABC):
    """Repository that perform CRUD operations on metainfo records."""

    def __init__(self, db) -> None:  # TODO: move to base class
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:  # TODO: move to base class
        """Start transaction."""
        return self.db.transaction()

    @abc.abstractmethod
    async def create_empty_metainfo(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> bool:
        """Return True if metainfo was created."""

    @abc.abstractmethod
    async def update_metainfo(
            self,
            user: domain.User,
            metainfo: domain.Metainfo,
    ) -> bool:
        """Return True if metainfo was updated."""

    @abc.abstractmethod
    async def read_metainfo(
            self,
            uuid: UUID,
    ) -> Optional[domain.Metainfo]:
        """Return Metainfo or None."""
