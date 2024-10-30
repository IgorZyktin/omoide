"""Use cases for browse page."""

from typing import NamedTuple
from uuid import UUID

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.omoide_app.common.common_use_cases import BaseAPPUseCase
from omoide.presentation import web

LOG = custom_logging.get_logger(__name__)


class BaseBrowseUseCase(BaseAPPUseCase):
    """Base class."""

    @staticmethod
    async def _ensure_allowed_to(
        user: models.User,
        item: models.Item,
        public_users: set[int],
    ) -> None:
        """Raise if user has no access to this item."""
        allowed_to = any(
            (
                user.is_admin,
                item.owner_id in public_users,
                item.owner_id == user.id,
                user.id in item.permissions,
            )
        )

        if not allowed_to:
            msg = 'You are not allowed to browse this'
            raise exceptions.NotAllowedError(msg)


class AppBrowseDynamicUseCase(BaseBrowseUseCase):
    """Use case for browse (application)."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> tuple[list[models.Item], models.Item, models.Metainfo]:
        """Return browse model suitable for rendering."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)

            public_users = await self.mediator.users.get_public_user_ids(conn)
            await self._ensure_allowed_to(user, item, public_users)

            parents = await self.mediator.items.get_parents(conn, item)
            metainfo = await self.mediator.meta.get_by_item(conn, item)

        return parents, item, metainfo


class BrowseResult(NamedTuple):
    """DTO for current use case."""

    item: models.Item
    parents: list[models.Item]
    metainfo: models.Metainfo
    total_items: int
    total_pages: int
    items: list[models.Item]
    names: list[str | None]
    aim: web.Aim


class AppBrowsePagedUseCase(BaseBrowseUseCase):
    """Use case for browse (application)."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        aim: web.Aim,
    ) -> BrowseResult:
        """Return browse model suitable for rendering."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)

            public_users = await self.mediator.users.get_public_user_ids(conn)
            await self._ensure_allowed_to(user, item, public_users)

            parents = await self.mediator.items.get_parents(conn, item)
            children = await self.mediator.browse.get_children(
                conn=conn,
                item=item,
                offset=aim.offset,
                limit=aim.items_per_page,
            )

            names = await self.mediator.browse.get_parent_names(conn, children)
            total_items = await self.mediator.items.count_children(conn, item)
            metainfo = await self.mediator.meta.get_by_item(conn, item)

        return BrowseResult(
            item=item,
            parents=parents,
            metainfo=metainfo,
            total_items=total_items,
            total_pages=aim.calc_total_pages(total_items),
            items=children,
            names=names,
            aim=aim,
        )
