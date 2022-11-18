# -*- coding: utf-8 -*-
"""Repository that performs all search queries.
"""
import abc

from omoide.domain import aim as aim_module
from omoide.domain import auth
from omoide.domain import common
from omoide.domain.interfaces.in_storage.in_repositories.in_rp_base import \
    AbsBaseRepository


class AbsSearchRepository(
    AbsBaseRepository,
):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def total_matching_anon(
            self,
            query: common.Query,
            aim: aim_module.Aim,
    ) -> int:
        """Count matching items for unauthorised user."""

    @abc.abstractmethod
    async def total_matching_known(
            self,
            user: auth.User,
            query: common.Query,
            aim: aim_module.Aim,
    ) -> int:
        """Return total matching items for authorised user."""

    @abc.abstractmethod
    async def search_dynamic_anon(
            self,
            query: common.Query,
            details: common.Details,
            aim: aim_module.Aim,
    ) -> list[common.Item]:
        """Find items for unauthorised user."""

    @abc.abstractmethod
    async def search_dynamic_known(
            self,
            user: auth.User,
            query: common.Query,
            details: common.Details,
            aim: aim_module.Aim,
    ) -> list[common.Item]:
        """Find items for authorised user."""

    @abc.abstractmethod
    async def search_paged_anon(
            self,
            query: common.Query,
            details: common.Details,
            aim: aim_module.Aim,
    ) -> list[common.Item]:
        """Find items for unauthorised user."""

    @abc.abstractmethod
    async def search_paged_known(
            self,
            user: auth.User,
            query: common.Query,
            details: common.Details,
            aim: aim_module.Aim,
    ) -> list[common.Item]:
        """Find items for authorised user."""
