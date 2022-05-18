# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces import repositories


class AbsItemsRepository(repositories.AbsRepository, abc.ABC):
    """Repository that perform CRUD operations on items and their data."""

    @abc.abstractmethod
    async def generate_uuid(self) -> UUID:
        """Generate new UUID4 for an item."""

    @abc.abstractmethod
    async def create_item(
            self,
            user: domain.User,
            payload: domain.CreateItemIn,
    ) -> UUID:
        """Return UUID for created item."""

    @abc.abstractmethod
    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return item or None."""

    @abc.abstractmethod
    async def delete_item(
            self,
            uuid: UUID,
    ) -> None:
        """Delete item with given UUID."""
