"""Use cases for browse page."""

from typing import NamedTuple
from uuid import UUID

from omoide import custom_logging
from omoide import domain
from omoide import exceptions
from omoide import models
from omoide.omoide_app.common.common_use_cases import BaseAPPUseCase

LOG = custom_logging.get_logger(__name__)


class BaseBrowseUseCase(BaseAPPUseCase):
    """Base class."""

    async def _ensure_allowed_to(
        self,
        user: models.User,
        item: models.Item,
    ) -> None:
        """Raise if user has no access to this item."""
        public_users = (
            await self.mediator.users_repo.get_public_user_uuids()
        )

        allowed_to = any(
            (
                user.is_admin,
                item.owner_uuid in public_users,
                item.owner_uuid == user.uuid,
                str(user.uuid) in item.permissions,
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
        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)

            await self._ensure_allowed_to(user, item)

            parents = await self.mediator.items_repo.get_parents(item)
            metainfo = await self.mediator.meta_repo.read_metainfo(item)

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
    aim: domain.Aim


class AppBrowsePagedUseCase(BaseBrowseUseCase):
    """Use case for browse (application)."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        aim: domain.Aim,
    ) -> BrowseResult:
        """Return browse model suitable for rendering."""
        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)

            await self._ensure_allowed_to(user, item)

            parents = await self.mediator.items_repo.get_parents(item)
            children = await self.mediator.browse_repo.get_children(
                item=item,
                offset=aim.offset,
                limit=aim.items_per_page,
            )

            names = await self.mediator.browse_repo.get_parent_names(children)
            total_items = await self.mediator.browse_repo.count_children(item)
            metainfo = await self.mediator.meta_repo.read_metainfo(item)

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
