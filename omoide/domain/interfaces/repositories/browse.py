# -*- coding: utf-8 -*-
"""Repository that performs all browse queries.
"""
import abc
from uuid import UUID

from omoide import domain
from omoide.domain import common
from omoide.domain.interfaces.repositories.base import AbsRepository
from omoide.domain.interfaces.repositories.items import AbsItemsRepository


class AbsBrowseRepository(
    AbsItemsRepository,
    AbsRepository,
):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def get_children(
            self,
            item_uuid: str,
            details: common.Details,
    ) -> list[common.Item]:
        """Load all children with all required fields."""

    @abc.abstractmethod
    async def count_items(
            self,
            item_uuid: str,
    ) -> int:
        """Count all children with all required fields."""

    @abc.abstractmethod
    async def get_specific_children(
            self,
            user: domain.User,
            item_uuid: str,
            details: common.Details,
    ) -> list[common.Item]:
        """Load all children with all required fields (and access)."""

    @abc.abstractmethod
    async def count_specific_items(
            self,
            user: domain.User,
            item_uuid: str,
    ) -> int:
        """Count all children with all required fields (and access)."""

    @abc.abstractmethod
    async def dynamic_children_for_anon(
            self,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Load all children for given UUID (for Anon)."""

    @abc.abstractmethod
    async def dynamic_children_for_known(
            self,
            user: domain.User,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Load all children for given UUID (for known user)."""
