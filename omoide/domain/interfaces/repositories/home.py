# -*- coding: utf-8 -*-
"""Repository that performs all search queries.
"""
import abc

from omoide.domain import aim as aim_module
from omoide.domain import common, auth
from omoide.domain.interfaces.repositories.base import AbsRepository


class AbsHomeRepository(AbsRepository):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def find_home_items_for_anon(
            self,
            aim: aim_module.Aim,
    ) -> list[common.Item]:
        """Find home items for unauthorised user."""

    @abc.abstractmethod
    async def find_home_items_for_known(
            self,
            user: auth.User,
            aim: aim_module.Aim,
    ) -> list[common.Item]:
        """Find home items for known user."""
