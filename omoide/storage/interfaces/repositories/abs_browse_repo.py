"""Repository that performs all browse queries."""
import abc
from typing import Optional
from uuid import UUID

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
    ) -> Optional[common.Location]:
        """Return Location of the item."""

    @abc.abstractmethod
    async def get_item_with_position(
        self,
        user: models.User,
        item_uuid: UUID,
        child_uuid: UUID,
        aim: common.Aim,
    ) -> Optional[common.PositionedItem]:
        """Return item with its position in siblings."""

    @abc.abstractmethod
    async def simple_find_items_to_browse(
        self,
        user: models.User,
        uuid: Optional[UUID],
        aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items to browse depending on parent (simple)."""

    @abc.abstractmethod
    async def complex_find_items_to_browse(
        self,
        user: models.User,
        uuid: Optional[UUID],
        aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items to browse depending on parent (including inheritance)."""

    @abc.abstractmethod
    async def get_recent_items(
        self,
        user: models.User,
        aim: domain.Aim,
    ) -> list[domain.Item]:
        """Return portion of recently loaded items."""

    @abc.abstractmethod
    async def get_parents_names(
        self,
        items: list[domain.Item],
    ) -> list[Optional[str]]:
        """Get names of parents of the given items."""
