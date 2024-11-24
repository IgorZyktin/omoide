"""Common use case elements."""

from typing import Any
from uuid import UUID
from uuid import uuid4

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator

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

    async def create_one_item(  # noqa: PLR0913 Too many arguments in function definition
        self,
        conn: Any,  # TODO - find a way to skip this argument
        user: models.User,
        uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str,
        number: int | None,
        is_collection: bool,
        tags: list[str],
        permissions: list[dict[str, UUID | str]],
        top_level: bool = False,
    ) -> models.Item:
        """Create single item."""
        if uuid is None:
            valid_uuid = uuid4()
        else:
            valid_uuid = uuid

        msg = 'You are not allowed to create items for other users'

        if top_level:
            parent = None
        elif parent_uuid is None:
            parent = await self.mediator.users.get_root_item(conn, user)
        else:
            parent = await self.mediator.items.get_by_uuid(conn, parent_uuid)
            if parent.owner_uuid != user.uuid:
                raise exceptions.NotAllowedError(msg)

        _permissions: set[int] = set()
        for human_readable_user in permissions:
            user_uuid = human_readable_user.get('uuid')
            if not isinstance(user_uuid, UUID):
                continue
            user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            _permissions.add(user.id)

        item = models.Item(
            id=-1,
            uuid=valid_uuid,
            parent_id=parent.id if parent is not None else None,
            parent_uuid=parent.uuid if parent is not None else None,
            owner_id=user.id,
            owner_uuid=user.uuid,
            name=name,
            status=models.Status.AVAILABLE if is_collection else models.Status.CREATED,
            number=number or -1,
            is_collection=is_collection,
            content_ext=None,
            preview_ext=None,
            thumbnail_ext=None,
            tags=set(tags),
            permissions=_permissions,
            extras={},
        )

        item.id = await self.mediator.items.create(conn, item)

        metainfo = models.Metainfo(
            item_id=item.id,
            created_at=utils.now(),
            updated_at=utils.now(),
            deleted_at=None,
            user_time=None,
            content_type=None,
            content_size=None,
            preview_size=None,
            thumbnail_size=None,
            content_width=None,
            content_height=None,
            preview_width=None,
            preview_height=None,
            thumbnail_width=None,
            thumbnail_height=None,
        )

        await self.mediator.meta.create(conn, metainfo)

        return item
