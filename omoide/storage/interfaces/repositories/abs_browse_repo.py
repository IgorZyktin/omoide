"""Repository that performs all browse queries."""
import abc
from uuid import UUID

from omoide import const
from omoide import domain
from omoide import models
from omoide.domain import common
from omoide.storage import interfaces as storage_interfaces


class AbsBrowseRepository(abc.ABC):
    """Repository that performs all browse queries."""

    @abc.abstractmethod
    async def get_children(
        self,
        user: models.User,
        uuid: UUID,
        aim: common.Aim,
    ) -> list[common.Item]:
        """Load all children of an item with given UUID."""

    @abc.abstractmethod
    async def count_children(
        self,
        user: models.User,
        uuid: UUID,
    ) -> int:
        """Count all children of an item with given UUID."""

    @abc.abstractmethod
    async def get_location(
        self,
        user: models.User,
        uuid: UUID,
        aim: common.Aim,
        users_repo: storage_interfaces.AbsUsersRepo,
    ) -> common.Location | None:
        """Return Location of the item."""

    @abc.abstractmethod
    async def get_item_with_position(
        self,
        user: models.User,
        item_uuid: UUID,
        child_uuid: UUID,
        aim: common.Aim,
    ) -> common.PositionedItem | None:
        """Return item with its position in siblings."""

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
    async def browse_associated_anon(
        self,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items to browse depending on parent (all children)."""

    @abc.abstractmethod
    async def browse_associated_known(
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
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return recently updated items."""

    # FIXME - delete this method
    @abc.abstractmethod
    async def get_parents_names(
        self,
        items: list[domain.Item],
    ) -> list[str | None]:
        """Get names of parents of the given items."""

    @abc.abstractmethod
    async def get_parent_names(
        self,
        items: list[models.Item],
    ) -> list[str | None]:
        """Get names of parents of the given items."""
