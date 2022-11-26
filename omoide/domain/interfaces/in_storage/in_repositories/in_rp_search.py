# -*- coding: utf-8 -*-
"""Repository that performs all search queries.
"""
import abc

from omoide.domain import auth
from omoide.domain import common
from omoide.domain.interfaces.in_storage.in_repositories.in_rp_base import \
    AbsBaseRepository


class AbsSearchRepository(
    AbsBaseRepository,
):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def count_matching_items(
            self,
            user: auth.User,
            aim: common.Aim,
    ) -> int:
        """Count matching items for search query."""

    @abc.abstractmethod
    async def get_matching_items(
            self,
            user: auth.User,
            aim: common.Aim,
    ) -> list[common.Item]:
        """Return matching items for search query."""
