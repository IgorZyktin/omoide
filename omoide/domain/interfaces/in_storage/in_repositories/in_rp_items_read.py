# -*- coding: utf-8 -*-
"""Repository that performs basic read operations on items.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsItemsReadRepository(in_rp_base.AbsBaseRepository):
    """Repository that performs basic read operations on items."""

    @abc.abstractmethod
    async def check_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Check access to the Item with given UUID for the given User."""

    @abc.abstractmethod
    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return Item or None."""

    @abc.abstractmethod
    async def read_children_of(
            self,
            user: domain.User,
            item: domain.Item,
            ignore_collections: bool,
    ) -> list[domain.Item]:
        """Return all direct descendants of the given item."""

    @abc.abstractmethod
    async def get_simple_location(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
    ) -> Optional[domain.SimpleLocation]:
        """Return Location of the item (without pagination)."""

    @abc.abstractmethod
    async def count_items_by_owner(
            self,
            user: domain.User,
            only_collections: bool = False,
    ) -> int:
        """Return total amount of items for given user uuid."""

    @abc.abstractmethod
    async def count_all_children_of(
            self,
            item: domain.Item,
    ) -> int:
        """Count dependant items."""

    @abc.abstractmethod
    async def get_all_parents(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> list[domain.Item]:
        """Return all parents of the given item."""

    @abc.abstractmethod
    async def get_direct_children_uuids_of(
            self,
            user: domain.User,
            item_uuid: UUID,
    ) -> list[UUID]:
        """Return all direct items of th given item."""

    @abc.abstractmethod
    async def read_computed_tags(
            self,
            uuid: UUID,
    ) -> list[str]:
        """Return all computed tags for the item."""

    @abc.abstractmethod
    async def read_item_by_name(
            self,
            user: domain.User,
            name: str,
    ) -> domain.Item | None:
        """Return corresponding item."""
