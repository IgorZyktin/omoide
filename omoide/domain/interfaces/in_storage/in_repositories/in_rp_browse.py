# -*- coding: utf-8 -*-
"""Repository that performs all browse queries.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import common
from omoide.domain.interfaces.in_storage.in_repositories import \
    in_rp_base
from omoide.domain.interfaces.in_storage.in_repositories import \
    in_rp_users_read


class AbsBrowseRepository(
    in_rp_base.AbsBaseRepository
):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def get_children(
            self,
            uuid: UUID,
            details: common.Details,
    ) -> list[common.Item]:
        """Load all children with all required fields."""

    @abc.abstractmethod
    async def count_items(
            self,
            uuid: UUID,
    ) -> int:
        """Count all children with all required fields."""

    @abc.abstractmethod
    async def get_specific_children(
            self,
            user: domain.User,
            uuid: UUID,
            details: common.Details,
    ) -> list[common.Item]:
        """Load all children with all required fields (and access)."""

    @abc.abstractmethod
    async def count_specific_items(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> int:
        """Count all children with all required fields (and access)."""

    @abc.abstractmethod
    async def get_simple_location(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
    ) -> Optional[domain.SimpleLocation]:
        """Return Location of the item (without pagination)."""

    @abc.abstractmethod
    async def get_location(
            self,
            user: domain.User,
            uuid: UUID,
            details: common.Details,
            users_repo: in_rp_users_read.AbsUsersReadRepository,
    ) -> Optional[common.Location]:
        """Return Location of the item."""

    @abc.abstractmethod
    async def get_item_with_position(
            self,
            user: domain.User,
            item_uuid: UUID,
            child_uuid: UUID,
            details: common.Details,
    ) -> Optional[common.PositionedItem]:
        """Return item with its position in siblings."""
