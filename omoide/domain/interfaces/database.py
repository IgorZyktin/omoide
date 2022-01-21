# -*- coding: utf-8 -*-
"""Repository interfaces.
"""
import abc

from omoide.domain import auth, browse, common, preview, search


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


class AbsSearchRepository(AbsRepository):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def count_for_anon_user(self, user: auth.User) -> int:
        """Count available items for unauthorised user."""

    @abc.abstractmethod
    async def search_random_items_for_anon_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find random items for unauthorised user."""

    @abc.abstractmethod
    async def search_specific_items_for_anon_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find specific items for unauthorised user."""

    @abc.abstractmethod
    async def count_for_known_user(self, user: auth.User) -> int:
        """Count available items for authorised user."""

    @abc.abstractmethod
    async def search_random_items_for_known_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find random items for authorised user."""

    @abc.abstractmethod
    async def search_specific_items_for_known_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
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
    async def get_nested_items(
            self,
            user: auth.User,
            item_uuid: str,
            query: browse.Query,
    ) -> tuple[browse.Result, browse.AccessStatus]:  # FIXME
        """Load all children with all required fields."""
