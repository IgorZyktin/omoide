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
    async def total_random_anon(
            self
    ) -> int:
        """Count all available items for unauthorised user."""

    @abc.abstractmethod
    async def total_specific_anon(
            self,
            query: common.Query,
    ) -> int:
        """Count specific available items for unauthorised user."""

    @abc.abstractmethod
    async def search_random_anon(
            self,
            query: common.Query,
            details: common.Details,
    ) -> list[common.Item]:
        """Find random items for unauthorised user."""

    @abc.abstractmethod
    async def search_specific_anon(
            self,
            query: common.Query,
            details: common.Details,
    ) -> list[common.Item]:
        """Find specific items for unauthorised user."""

    @abc.abstractmethod
    async def total_random_known(
            self,
            user: auth.User,
    ) -> int:
        """Count all available items for authorised user."""

    @abc.abstractmethod
    async def total_specific_known(
            self,
            user: auth.User,
            query: common.Query,
    ) -> int:
        """Count available items for authorised user."""

    @abc.abstractmethod
    async def search_random_known(
            self,
            user: auth.User,
            query: common.Query,
            details: common.Details,
    ) -> list[common.Item]:
        """Find random items for authorised user."""

    @abc.abstractmethod
    async def search_specific_known(
            self,
            user: auth.User,
            query: common.Query,
            details: common.Details,
    ) -> list[common.Item]:
        """Find specific items for authorised user."""
