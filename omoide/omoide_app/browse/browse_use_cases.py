"""Use cases for browse page."""

from typing import NamedTuple
from uuid import UUID

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.presentation import web

LOG = custom_logging.get_logger(__name__)


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


class BrowseDynamicResult(NamedTuple):
    """Pre-filled context for the dynamic (infinite-scroll) browse page."""

    parents: list[models.Item]
    item: models.Item
    metainfo: models.Metainfo


class AppBrowseDynamicUseCase:
    """Use case for browse (application)."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> BrowseDynamicResult:
        """Return browse model suitable for rendering."""
        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)

            public_users = await self.users.get_public_user_ids(conn)
            await _ensure_allowed_to(user, item, public_users)

            parents = await self.items.get_parents(conn, item)
            metainfo = await self.meta.get_by_item(conn, item)

        return BrowseDynamicResult(parents=parents, item=item, metainfo=metainfo)


class BrowseResult(NamedTuple):
    """DTO for current use case."""

    item: models.Item
    parents: list[models.Item]
    metainfo: models.Metainfo
    total_items: int
    total_pages: int
    items: list[models.Item]
    names: dict[int, str | None]
    aim: web.Aim


class AppBrowsePagedUseCase:
    """Use case for browse (application)."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        aim: web.Aim,
    ) -> BrowseResult:
        """Return browse model suitable for rendering."""
        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)

            public_users = await self.users.get_public_user_ids(conn)
            await _ensure_allowed_to(user, item, public_users)

            parents = await self.items.get_parents(conn, item)
            children = await self.items.get_children(
                conn=conn,
                item=item,
                offset=aim.offset,
                limit=aim.items_per_page,
            )

            names = await self.items.get_parent_names(conn, children)
            total_items = await self.items.count_children(conn, item)
            metainfo = await self.meta.get_by_item(conn, item)

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
