# -*- coding: utf-8 -*-
"""Repository that performs all search queries.
"""
import abc

from omoide import domain
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
            user: domain.User,
            guess: domain.GuessTag,
            obligation: domain.Obligation,
    ) -> list[domain.GuessResult]:
        """Guess tag for known user."""

    @abc.abstractmethod
    async def guess_tag_anon(
            self,
            user: domain.User,
            guess: domain.GuessTag,
            obligation: domain.Obligation,
    ) -> list[domain.GuessResult]:
        """Guess tag for anon user."""
