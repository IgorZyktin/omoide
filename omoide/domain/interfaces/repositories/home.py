# -*- coding: utf-8 -*-
"""Repository that performs all search queries.
"""
import abc

from omoide.domain import common, auth
from omoide.domain.interfaces.repositories.base import AbsRepository


class AbsHomeRepository(AbsRepository):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def select_home_random_nested_anon(
            self,
    ) -> list[common.Item]:
        """Find random nested items for unauthorised user."""

    @abc.abstractmethod
    async def select_home_ordered_nested_anon(
            self,
    ) -> list[common.Item]:
        """Find ordered nested items for unauthorised user."""

    @abc.abstractmethod
    async def select_home_random_flat_anon(
            self,
    ) -> list[common.Item]:
        """Find random flat items for unauthorised user."""

    @abc.abstractmethod
    async def select_home_ordered_flat_anon(
            self,
    ) -> list[common.Item]:
        """Find ordered flat items for unauthorised user."""

    @abc.abstractmethod
    async def select_home_random_nested_known(
            self,
            user: auth.User,
    ) -> list[common.Item]:
        """Find random nested items for authorised user."""

    @abc.abstractmethod
    async def select_home_ordered_nested_known(
            self,
            user: auth.User,
    ) -> list[common.Item]:
        """Find ordered nested items for authorised user."""

    @abc.abstractmethod
    async def select_home_random_flat_known(
            self,
            user: auth.User,
    ) -> list[common.Item]:
        """Find random flat items for authorised user."""

    @abc.abstractmethod
    async def select_home_ordered_flat_known(
            self,
            user: auth.User,
    ) -> list[common.Item]:
        """Find ordered flat items for authorised user."""
