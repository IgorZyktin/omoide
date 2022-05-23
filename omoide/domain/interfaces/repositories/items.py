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
    async def check_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Check if user has access to the item."""

    @abc.abstractmethod
    async def assert_has_access(
            self,
            user: domain.User,
            uuid: UUID,
            only_for_owner: bool,
    ) -> None:
        """Raise if item does not exist or user has no access to it."""

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

    async def update_item(
            self,
            payload: domain.UpdateItemIn,
    ) -> UUID:
        """Update existing item."""

    @abc.abstractmethod
    async def delete_item(
            self,
            uuid: UUID,
    ) -> None:
        """Delete item with given UUID."""

    @abc.abstractmethod
    async def count_children(
            self,
            uuid: UUID,
    ) -> int:
        """Count dependant items (including the parent itself)."""
