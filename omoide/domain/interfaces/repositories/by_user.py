# -*- coding: utf-8 -*-
"""Repository that performs search by owner uuid.
"""
import abc

from omoide.domain import common, auth
from omoide.domain.interfaces.repositories.base import AbsRepository


class AbsByUserRepository(AbsRepository):
    """Repository that performs search by owner uuid."""

    @abc.abstractmethod
    async def count_items_of_public_user(
            self,
            owner_uuid: str,
    ) -> int:
        """Count all items of a public user."""

    @abc.abstractmethod
    async def get_items_of_public_user(
            self,
            owner_uuid: str,
            limit: int,
            offset: int,
    ) -> list[common.Item]:
        """Load all items of a public user."""

    @abc.abstractmethod
    async def count_items_of_private_user(
            self,
            user: auth.User,
            owner_uuid: str,
    ) -> int:
        """Count all items of a private user."""

    @abc.abstractmethod
    async def get_items_of_private_user(
            self,
            user: auth.User,
            owner_uuid: str,
            limit: int,
            offset: int,
    ) -> list[common.Item]:
        """Load all items of a private user."""
