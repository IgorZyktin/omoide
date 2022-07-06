# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on media records.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces import repositories
from omoide.presentation import api_models


class AbsMediaRepository(repositories.AbsRepository, abc.ABC):
    """Repository that perform CRUD operations on media records.
    """

    @abc.abstractmethod
    async def create_or_update_media(
            self,
            user: domain.User,
            payload: api_models.CreateMediaIn,
    ) -> bool:
        """Return True if media was created."""

    @abc.abstractmethod
    async def read_media(
            self,
            uuid: UUID,
    ) -> Optional[domain.Media]:
        """Return media or None."""

    @abc.abstractmethod
    async def delete_media(
            self,
            uuid: UUID,
    ) -> bool:
        """Delete media with given UUID."""
