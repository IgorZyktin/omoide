# -*- coding: utf-8 -*-
"""Repository that performs basic read operations on items.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide.application import app_models
from omoide.domain import models
from omoide.domain.interfaces.in_storage import in_rp_base


class AbsItemsReadRepository(in_rp_base.AbsBaseRepository):
    """Repository that performs basic read operations on items."""

    @abc.abstractmethod
    async def check_access(
            self,
            user: models.User,
            uuid: UUID,
    ) -> models.AccessStatus:
        """Check access to the Item with given UUID for the given User."""

    @abc.abstractmethod
    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[models.Item]:
        """Return Item or None."""

    @abc.abstractmethod
    async def read_children_of(
            self,
            user: models.User,
            item: models.Item,
            ignore_collections: bool,
    ) -> list[models.Item]:
        """Return all direct descendants of the given item."""

    @abc.abstractmethod
    async def get_simple_location(
            self,
            user: models.User,
            owner: models.User,
            item: models.Item,
    ) -> Optional[app_models.SimpleLocation]:
        """Return Location of the item (without pagination)."""

    @abc.abstractmethod
    async def count_items_by_owner(
            self,
            user: models.User,
            only_collections: bool = False,
    ) -> int:
        """Return total amount of items for given user uuid."""

    @abc.abstractmethod
    async def count_all_children_of(
            self,
            item: models.Item,
    ) -> int:
        """Count dependant items."""

    @abc.abstractmethod
    async def get_all_parents(
            self,
            user: models.User,
            item: models.Item,
    ) -> list[models.Item]:
        """Return all parents of the given item."""

    @abc.abstractmethod
    async def get_direct_children_uuids_of(
            self,
            user: models.User,
            item_uuid: UUID,
    ) -> list[UUID]:
        """Return all direct items of th given item."""

    @abc.abstractmethod
    async def read_computed_tags(
            self,
            uuid: UUID,
    ) -> list[str]:
        """Return all computed tags for the item."""
