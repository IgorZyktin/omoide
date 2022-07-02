# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces import repositories
from omoide.presentation import api_models


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
            payload: api_models.CreateItemIn,
    ) -> UUID:
        """Return UUID for created item."""

    @abc.abstractmethod
    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return item or None."""

    async def read_children(
            self,
            uuid: UUID,
    ) -> list[domain.Item]:
        """Return all direct descendants of the given item."""

    async def update_item(
            self,
            payload: api_models.UpdateItemIn,
    ) -> UUID:
        """Update existing item."""

    @abc.abstractmethod
    async def delete_item(
            self,
            uuid: UUID,
    ) -> None:
        """Delete item with given UUID."""

    @abc.abstractmethod
    async def count_all_children(
            self,
            uuid: UUID,
    ) -> int:
        """Count dependant items (including the parent itself)."""

    @abc.abstractmethod
    async def get_simple_location(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
    ) -> Optional[domain.SimpleLocation]:
        """Return Location of the item (without pagination)."""

    @abc.abstractmethod
    async def simple_find_items_to_browse(
            self,
            user: domain.User,
            uuid: Optional[UUID],
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items to browse depending on parent (simple)."""

    @abc.abstractmethod
    async def complex_find_items_to_browse(
            self,
            user: domain.User,
            uuid: Optional[UUID],
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items to browse depending on parent (including inheritance)."""

    @abc.abstractmethod
    async def update_tags_in_children(
            self,
            item: domain.Item,
    ) -> None:
        """Apply parent tags to every item (and their children too)."""
