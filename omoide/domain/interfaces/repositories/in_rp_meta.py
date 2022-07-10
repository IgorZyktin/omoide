# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on meta records.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces import repositories


class AbsMetaRepository(repositories.AbsRepository, abc.ABC):
    """Repository that perform CRUD operations on meta records."""

    @abc.abstractmethod
    async def create_or_update_meta(
            self,
            user: domain.User,
            meta: domain.Meta,
    ) -> bool:
        """Return True if meta was created."""

    @abc.abstractmethod
    async def read_meta(
            self,
            uuid: UUID,
    ) -> Optional[domain.Meta]:
        """Return Meta or None."""
