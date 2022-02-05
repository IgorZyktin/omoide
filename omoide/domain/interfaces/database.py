# -*- coding: utf-8 -*-
"""Repository interfaces.
"""
import abc
from typing import Optional

from omoide.domain import auth, common, preview


class AbsRepository(abc.ABC):
    """Base repository class."""

    @abc.abstractmethod
    def transaction(self):
        """Start transaction."""

    @abc.abstractmethod
    async def check_access(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> common.AccessStatus:
        """Check if user has access to the item."""

    @abc.abstractmethod
    async def get_location(self, item_uuid: str) -> common.Location:
        """Return Location of the item."""

    @abc.abstractmethod
    async def get_user(
            self,
            user_uuid: str,
    ) -> Optional[common.SimpleUser]:
        """Return user or None."""

    @abc.abstractmethod
    async def get_item(
            self,
            item_uuid: str,
    ) -> Optional[common.Item]:
        """Return item or None."""

    @abc.abstractmethod
    async def get_item_with_position(
            self,
            item_uuid: str,
    ) -> Optional[common.PositionedItem]:
        """Return item with its position in siblings."""


class AbsSearchRepository(AbsRepository):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def total_random_anon(
            self,
            user: auth.User,
    ) -> int:
        """Count all available items for unauthorised user."""

    @abc.abstractmethod
    async def total_specific_anon(
            self,
            user: auth.User,
            query: common.Query,
    ) -> int:
        """Count specific available items for unauthorised user."""

    @abc.abstractmethod
    async def search_random_anon(
            self,
            user: auth.User,
            query: common.Query,
    ) -> list[common.Item]:
        """Find random items for unauthorised user."""

    @abc.abstractmethod
    async def search_specific_anon(
            self,
            user: auth.User,
            query: common.Query,
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
    ) -> list[common.Item]:
        """Find random items for authorised user."""

    @abc.abstractmethod
    async def search_specific_known(
            self,
            user: auth.User,
            query: common.Query,
    ) -> list[common.Item]:
        """Find specific items for authorised user."""


class AbsPreviewRepository(AbsRepository):
    """Repository that performs all preview queries."""

    @abc.abstractmethod
    async def get_preview_item(self, item_uuid: str) -> preview.Item:
        """Return instance of the item."""

    @abc.abstractmethod
    async def get_neighbours(self, item_uuid: str) -> list[str]:
        """Return uuids of all the neighbours."""


class AbsBrowseRepository(AbsRepository):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def get_items(
            self,
            item_uuid: str,
            query: common.Query,
    ) -> list[common.Item]:
        """Load all children with all required fields."""

    @abc.abstractmethod
    async def count_items(
            self,
            item_uuid: str,
    ) -> int:
        """Count all children with all required fields."""


class AbsByUserRepository(AbsRepository):
    """Repository that performs search by owner uuid."""

    @abc.abstractmethod
    async def user_is_public(
            self,
            owner_uuid: str,
    ) -> bool:
        """Return True if owner is a public user."""

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
