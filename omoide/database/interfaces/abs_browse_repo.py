"""Repository that performs all browse queries."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsBrowseRepo(abc.ABC, Generic[ConnectionT]):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def browse_direct_anon(
        self,
        conn: ConnectionT,
        item: models.Item,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""

    @abc.abstractmethod
    async def browse_direct_known(
        self,
        conn: ConnectionT,
        user: models.User,
        item: models.Item,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (only direct)."""

    @abc.abstractmethod
    async def browse_related_anon(
        self,
        conn: ConnectionT,
        item: models.Item,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""

    @abc.abstractmethod
    async def browse_related_known(
        self,
        conn: ConnectionT,
        user: models.User,
        item: models.Item,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""

    @abc.abstractmethod
    async def get_recently_updated_items_anon(
        self,
        conn: ConnectionT,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return recently updated items."""

    @abc.abstractmethod
    async def get_recently_updated_items_known(
        self,
        conn: ConnectionT,
        user: models.User,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return recently updated items."""
