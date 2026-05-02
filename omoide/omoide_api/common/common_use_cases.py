"""Common use case elements."""

from typing import Any

from omoide import custom_logging
from omoide import models
from omoide.infra.mediators import Mediator

LOG = custom_logging.get_logger(__name__)


class BaseAPIUseCase:
    """Base use case class for API."""

    def __init__(self, mediator: Mediator) -> None:
        """Initialize instance."""
        self.mediator = mediator


class BaseItemUseCase(BaseAPIUseCase):
    """Base class for use cases that create items."""

    def __init__(self, mediator: Mediator) -> None:
        """Initialize instance."""
        super().__init__(mediator)
        self._users_cache: dict[int, models.User] = {}
        self._items_cache: dict[int, models.Item] = {}
        self._computed_tags_cache: dict[int, set[str]] = {}

    async def _get_cached_user(self, conn: Any, user_id: int) -> models.User:
        """Perform cached request."""
        user = self._users_cache.get(user_id)

        if user is not None:
            return user

        user = await self.mediator.users.get_by_id(conn, user_id)
        self._users_cache[user.id] = user
        return user

    async def _get_cached_item(self, conn: Any, item_id: int) -> models.Item:
        """Perform cached request."""
        item = self._items_cache.get(item_id)

        if item is not None:
            return item

        item = await self.mediator.items.get_by_id(conn, item_id)
        self._items_cache[item.id] = item
        return item

    async def _get_cached_computed_tags(self, conn: Any, item: models.Item) -> set[str]:
        """Perform cached request."""
        tags = self._computed_tags_cache.get(item.id)

        if tags is not None:
            return tags

        tags = await self.mediator.tags.get_computed_tags(conn, item)
        self._computed_tags_cache[item.id] = tags
        return tags
