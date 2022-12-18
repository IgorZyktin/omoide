# -*- coding: utf-8 -*-
"""Repository that performs write operations on items.
"""
import abc
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage \
    .in_repositories.in_rp_items_read import AbsItemsReadRepository


class AbsItemsWriteRepository(AbsItemsReadRepository):
    """Repository that performs write operations on items."""

    @abc.abstractmethod
    async def generate_item_uuid(self) -> UUID:
        """Generate new UUID4 for the item."""

    @abc.abstractmethod
    async def create_item(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> UUID:
        """Return UUID for created item."""

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

    @abc.abstractmethod
    async def update_tags_in_children_of(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> None:
        """Apply parent tags to every item (and their children too)."""

    @abc.abstractmethod
    async def check_child(
            self,
            possible_parent_uuid: UUID,
            possible_child_uuid: UUID,
    ) -> bool:
        """Return True if given item is actually a child."""

    @abc.abstractmethod
    async def update_permissions_in_parents(
            self,
            user: domain.User,
            item: domain.Item,
            added: set[UUID],
            deleted: set[UUID],
    ) -> None:
        """Apply new permissions to every parent."""

    @abc.abstractmethod
    async def update_permissions_in_children(
            self,
            user: domain.User,
            item: domain.Item,
            override: bool,
            added: set[UUID],
            deleted: set[UUID],
    ) -> None:
        """Apply new permissions to every child."""
