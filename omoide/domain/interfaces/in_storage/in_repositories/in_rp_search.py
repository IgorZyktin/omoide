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
            limit: int,
    ) -> list[common.Item]:
        """Return matching items for search query."""

    @abc.abstractmethod
    async def guess_tag_anon(
            self,
            text: str,
            limit: int,
    ) -> list[str]:
        """Guess tag for anon user."""

    @abc.abstractmethod
    async def guess_tag_known(
            self,
            user: auth.User,
            text: str,
            limit: int,
    ) -> list[str]:
        """Guess tag for known user."""
