# -*- coding: utf-8 -*-
"""Repository that performs all browse queries.
"""
import abc

from omoide.domain import common
from omoide.domain.interfaces.repositories.base import AbsRepository


class AbsBrowseRepository(AbsRepository):
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
