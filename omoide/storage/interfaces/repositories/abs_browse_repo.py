"""Repository that performs all browse queries."""

import abc
from uuid import UUID

from omoide import const
from omoide import models


class AbsBrowseRepository(abc.ABC):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def get_children(
        self,
        item: models.Item,
        offset: int | None,
        limit: int | None,
    ) -> list[models.Item]:
        """Load all children of given item."""

    @abc.abstractmethod
    async def count_children(self, item: models.Item) -> int:
        """Count all children of an item with given UUID."""

    @abc.abstractmethod
    async def browse_direct_anon(
        self,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""

    @abc.abstractmethod
    async def browse_direct_known(
        self,
        user: models.User,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""

    @abc.abstractmethod
    async def browse_related_anon(
        self,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""

    @abc.abstractmethod
    async def browse_related_known(
        self,
        user: models.User,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""

    @abc.abstractmethod
    async def get_recently_updated_items(
        self,
        user: models.User,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return recently updated items."""

    @abc.abstractmethod
    async def get_parent_names(
        self,
        items: list[models.Item],
    ) -> list[str | None]:
        """Get names of parents of the given items."""
