# -*- coding: utf-8 -*-
"""Base repository class.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import auth, common


class AbsRepository(abc.ABC):
    """Base repository class."""

    @abc.abstractmethod
    def transaction(self):
        """Start transaction."""

    @abc.abstractmethod
    async def generate_uuid(self) -> UUID:
        """Generate new UUID4."""

    @abc.abstractmethod
    async def check_access(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> common.AccessStatus:
        """Check if user has access to the item."""

    @abc.abstractmethod
    async def get_location(
            self,
            user: domain.User,
            item_uuid: str,
            details: common.Details,
    ) -> Optional[common.Location]:
        """Return Location of the item."""

    @abc.abstractmethod
    async def user_is_public(
            self,
            owner_uuid: str,
    ) -> bool:
        """Return True if owner is a public user."""

    @abc.abstractmethod
    async def get_user(
            self,
            user_uuid: str,
    ) -> Optional[auth.User]:
        """Return user or None."""

    @abc.abstractmethod
    async def get_user_by_login(
            self,
            user_login: str,
    ) -> Optional[auth.User]:
        """Return user or None."""

    @abc.abstractmethod
    async def get_positioned_by_user(
            self,
            user: auth.User,
            item: common.Item,
            details: common.Details,
    ) -> Optional[common.PositionedByUserItem]:
        """Return user with position information."""

    @abc.abstractmethod
    async def get_item(
            self,
            item_uuid: str,
    ) -> Optional[common.Item]:
        """Return item or None."""

    @abc.abstractmethod
    async def get_item_with_position(
            self,
            user: auth.User,
            item_uuid: str,
            child_uuid: str,
            details: common.Details,
    ) -> Optional[common.PositionedItem]:
        """Return item with its position in siblings."""
