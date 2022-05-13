# -*- coding: utf-8 -*-
"""Repository that show items at the home endpoint.
"""
from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base


class HomeRepository(
    base.BaseRepository,
    interfaces.AbsHomeRepository,
):
    """Repository that show items at the home endpoint."""

    async def select_home_random_nested_anon(
            self,
    ) -> list[domain.Item]:
        """Find random nested items for unauthorised user."""
        raise

    async def select_home_ordered_nested_anon(
            self,
    ) -> list[domain.Item]:
        """Find ordered nested items for unauthorised user."""
        raise

    async def select_home_random_flat_anon(
            self,
    ) -> list[domain.Item]:
        """Find random flat items for unauthorised user."""
        raise

    async def select_home_ordered_flat_anon(
            self,
    ) -> list[domain.Item]:
        """Find ordered flat items for unauthorised user."""
        raise

    async def select_home_random_nested_known(
            self,
            user: domain.User,
    ) -> list[domain.Item]:
        """Find random nested items for authorised user."""
        raise

    async def select_home_ordered_nested_known(
            self,
            user: domain.User,
    ) -> list[domain.Item]:
        """Find ordered nested items for authorised user."""
        raise

    async def select_home_random_flat_known(
            self,
            user: domain.User,
    ) -> list[domain.Item]:
        """Find random flat items for authorised user."""
        raise

    async def select_home_ordered_flat_known(
            self,
            user: domain.User,
    ) -> list[domain.Item]:
        """Find ordered flat items for authorised user."""
        raise
