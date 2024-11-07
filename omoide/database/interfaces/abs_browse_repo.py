"""Repository that performs all browse queries."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import const
from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsBrowseRepo(Generic[ConnectionT], abc.ABC):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def get_children(
        self,
        conn: ConnectionT,
        item: models.Item,
        offset: int | None,
        limit: int | None,
    ) -> list[models.Item]:
        """Load all children of given item."""

    @abc.abstractmethod
    async def browse_direct_anon(
        self,
        conn: ConnectionT,
        item: models.Item,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""

    @abc.abstractmethod
    async def browse_direct_known(
        self,
        conn: ConnectionT,
        user: models.User,
        item: models.Item,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""

    @abc.abstractmethod
    async def browse_related_anon(
        self,
        conn: ConnectionT,
        item: models.Item,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""

    @abc.abstractmethod
    async def browse_related_known(
        self,
        conn: ConnectionT,
        user: models.User,
        item: models.Item,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""

    @abc.abstractmethod
    async def get_recently_updated_items(
        self,
        conn: ConnectionT,
        user: models.User,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return recently updated items."""
