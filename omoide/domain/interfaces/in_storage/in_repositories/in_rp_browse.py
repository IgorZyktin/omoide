# -*- coding: utf-8 -*-
"""Repository that performs all browse queries.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide.application import app_models
from omoide.domain import common
from omoide.domain import models
from omoide.domain.interfaces.in_storage import in_rp_base
from omoide.domain.interfaces.in_storage \
    .in_repositories.in_rp_users_read import AbsUsersReadRepository


class AbsBrowseRepository(in_rp_base.AbsBaseRepository):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def get_children(
            self,
            user: models.User,
            uuid: UUID,
            aim: app_models.Aim,
    ) -> list[models.Item]:
        """Load all children of an item with given UUID."""

    @abc.abstractmethod
    async def count_children(
            self,
            user: models.User,
            uuid: UUID,
    ) -> int:
        """Count all children of an item with given UUID."""

    @abc.abstractmethod
    async def get_location(
            self,
            user: models.User,
            uuid: UUID,
            aim: app_models.Aim,
            users_repo: AbsUsersReadRepository,
    ) -> Optional[app_models.Location]:
        """Return Location of the item."""

    @abc.abstractmethod
    async def get_item_with_position(
            self,
            user: models.User,
            item_uuid: UUID,
            child_uuid: UUID,
            aim: app_models.Aim,
    ) -> Optional[app_models.PositionedItem]:
        """Return item with its position in siblings."""

    @abc.abstractmethod
    async def simple_find_items_to_browse(
            self,
            user: models.User,
            uuid: Optional[UUID],
            aim: app_models.Aim,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (simple)."""

    @abc.abstractmethod
    async def complex_find_items_to_browse(
            self,
            user: models.User,
            uuid: Optional[UUID],
            aim: app_models.Aim,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (including inheritance)."""

    @abc.abstractmethod
    async def get_recent_items(
            self,
            user: models.User,
            aim: app_models.Aim,
    ) -> list[models.Item]:
        """Return portion of recently loaded items."""

    @abc.abstractmethod
    async def get_parents_names(
            self,
            items: list[models.Item],
    ) -> list[Optional[str]]:
        """Get names of parents of the given items."""
