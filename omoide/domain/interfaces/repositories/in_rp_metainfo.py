# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on metainfo records.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.repositories import base


class AbsMetainfoRepository(base.AbsBaseRepository, abc.ABC):
    """Repository that perform CRUD operations on metainfo records."""

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
