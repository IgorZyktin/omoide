# -*- coding: utf-8 -*-
"""Base repository class.
"""
import abc
from typing import Any
from typing import Optional

from omoide.domain import auth
from omoide.domain import common


class AbsRepository(abc.ABC):
    """Base repository class."""

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:
        """Start transaction."""
        return self.db.transaction()

    @abc.abstractmethod
    async def get_location(
            self,
            user: auth.User,
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
    async def get_item_with_position(
            self,
            user: auth.User,
            item_uuid: str,
            child_uuid: str,
            details: common.Details,
    ) -> Optional[common.PositionedItem]:
        """Return item with its position in siblings."""
