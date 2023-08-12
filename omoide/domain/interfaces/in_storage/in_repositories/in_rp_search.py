# -*- coding: utf-8 -*-
"""Repository that performs all search queries.
"""
import abc

from omoide import domain
from omoide.domain import errors
from omoide.domain.core import core_models
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsSearchRepository(
    in_rp_base.AbsBaseRepository,
):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def count_matching_items(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> int:
        """Count matching items for search query."""

    @abc.abstractmethod
    async def get_matching_items(
            self,
            user: domain.User,
            aim: domain.Aim,
            obligation: domain.Obligation,
    ) -> list[domain.Item]:
        """Return matching items for search query."""

    @abc.abstractmethod
    async def guess_tag_known(
            self,
            user: core_models.User,
            user_input: str,
            limit: int,
    ) -> list[core_models.GuessResult]:
        """Guess tag for known user."""

    @abc.abstractmethod
    async def guess_tag_anon(
            self,
            user: core_models.User,
            user_input: str,
            limit: int,
    ) -> list[core_models.GuessResult]:
        """Guess tag for anon user."""

    @abc.abstractmethod
    async def count_all_tags(
            self,
            user: domain.User,
    ) -> list[tuple[str, int]]:
        """Return statistics for known tags."""
