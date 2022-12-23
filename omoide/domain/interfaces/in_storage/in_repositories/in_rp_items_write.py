# -*- coding: utf-8 -*-
"""Repository that performs write operations on items.
"""
import abc
import datetime
from typing import Collection
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
    async def mark_files_as_orphans(
            self,
            item: domain.Item,
            moment: datetime.datetime,
    ) -> None:
        """Mark corresponding files as useless."""

    @abc.abstractmethod
    async def delete_item(
            self,
            item: domain.Item,
    ) -> bool:
        """Delete item with given UUID."""

    @abc.abstractmethod
    async def check_child(
            self,
            possible_parent_uuid: UUID,
            possible_child_uuid: UUID,
    ) -> bool:
        """Return True if given item is actually a child."""

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

    @abc.abstractmethod
    async def update_permissions(
            self,
            uuid: UUID,
            override: bool,
            added: Collection[UUID],
            deleted: Collection[UUID],
            all_permissions: Collection[UUID],
    ) -> None:
        """Apply new permissions for given item UUID."""

    @abc.abstractmethod
    async def add_tags(
            self,
            uuid: UUID,
            tags: Collection[str],
    ) -> None:
        """Add new tags to computed tags of the item."""

    @abc.abstractmethod
    async def delete_tags(
            self,
            uuid: UUID,
            tags: Collection[str],
    ) -> None:
        """Remove tags from computed tags of the item."""
