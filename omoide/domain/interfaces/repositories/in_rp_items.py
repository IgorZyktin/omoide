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

    # TODO - remove this
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

    # TODO - move to a separate repo
    @abc.abstractmethod
    async def read_children(
            self,
            uuid: UUID,
    ) -> list[domain.Item]:
        """Return all direct descendants of the given item."""

    @abc.abstractmethod
    async def update_item(
            self,
            item: domain.Item,
    ) -> UUID:
        """Update existing item."""

    @abc.abstractmethod
    async def delete_item(
            self,
            uuid: UUID,
    ) -> bool:
        """Delete item with given UUID."""

    # TODO - move to a separate repo
    @abc.abstractmethod
    async def count_all_children(
            self,
            uuid: UUID,
    ) -> int:
        """Count dependant items (including the parent itself)."""

    # TODO - move to a separate repo
    @abc.abstractmethod
    async def update_tags_in_children(
            self,
            item: domain.Item,
    ) -> None:
        """Apply parent tags to every item (and their children too)."""

    # TODO - move to a separate repo
    @abc.abstractmethod
    async def check_child(
            self,
            possible_parent_uuid: UUID,
            possible_child_uuid: UUID,
    ) -> bool:
        """Return True if given item is actually a child."""

    # TODO - move to a separate repo
    @abc.abstractmethod
    async def update_permissions_in_parents(
            self,
            item: domain.Item,
            new_permissions: domain.NewPermissions,
    ) -> None:
        """Apply new permissions to every parent."""

    # TODO - move to a separate repo
    @abc.abstractmethod
    async def update_permissions_in_children(
            self,
            item: domain.Item,
            new_permissions: domain.NewPermissions,
    ) -> None:
        """Apply new permissions to every child."""
