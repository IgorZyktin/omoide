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
    async def count_matching_anon(
            self,
            aim: common.Aim,
    ) -> int:
        """Count matching items for unauthorised user."""

    @abc.abstractmethod
    async def count_matching_known(
            self,
            user: auth.User,
            aim: common.Aim,
    ) -> int:
        """Return total matching items for authorised user."""

    @abc.abstractmethod
    async def search_dynamic_anon(
            self,
            aim: common.Aim,
    ) -> list[common.Item]:
        """Find items for unauthorised user."""

    @abc.abstractmethod
    async def search_dynamic_known(
            self,
            user: auth.User,
            aim: common.Aim,
    ) -> list[common.Item]:
        """Find items for authorised user."""

    @abc.abstractmethod
    async def search_paged_anon(
            self,
            aim: common.Aim,
    ) -> list[common.Item]:
        """Find items for unauthorised user."""

    @abc.abstractmethod
    async def search_paged_known(
            self,
            user: auth.User,
            aim: common.Aim,
    ) -> list[common.Item]:
        """Find items for authorised user."""
