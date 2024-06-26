# -*- coding: utf-8 -*-
"""Repository that performs all browse queries.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import common
from omoide.domain.interfaces.in_storage \
    .in_repositories.in_rp_base import AbsBaseRepository
from omoide.domain.interfaces.in_storage \
    .in_repositories.in_rp_users_read import AbsUsersRepository


class AbsBrowseRepository(
    AbsBaseRepository
):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def get_children(
            self,
            user: domain.User,
            uuid: UUID,
            aim: common.Aim,
    ) -> list[common.Item]:
        """Load all children of an item with given UUID."""

    @abc.abstractmethod
    async def count_children(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> int:
        """Count all children of an item with given UUID."""

    @abc.abstractmethod
    async def get_location(
            self,
            user: domain.User,
            uuid: UUID,
            aim: common.Aim,
            users_repo: AbsUsersRepository,
    ) -> Optional[common.Location]:
        """Return Location of the item."""

    @abc.abstractmethod
    async def get_item_with_position(
            self,
            user: domain.User,
            item_uuid: UUID,
            child_uuid: UUID,
            aim: common.Aim,
    ) -> Optional[common.PositionedItem]:
        """Return item with its position in siblings."""

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
    async def get_recent_items(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Return portion of recently loaded items."""

    @abc.abstractmethod
    async def get_parents_names(
            self,
            items: list[domain.Item],
    ) -> list[Optional[str]]:
        """Get names of parents of the given items."""
