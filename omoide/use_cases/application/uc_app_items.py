"""Use case for items."""
from uuid import UUID

from omoide import domain
from omoide import interfaces
from omoide import models
from omoide.domain import actions
from omoide.domain import errors
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage import interfaces as storage_interfaces

__all__ = [
    'AppItemUpdateUseCase',
    'AppItemDeleteUseCase',
]


class AppItemUpdateUseCase:
    """Use case for item modification page."""

    def __init__(
            self,
            users_repo: storage_interfaces.AbsUsersRepo,
            items_repo: storage_interfaces.AbsItemsRepo,
            metainfo_repo: storage_interfaces.AbsMetainfoRepo,
    ) -> None:
        """Initialize instance."""
        self.users_repo = users_repo
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: models.User,
            uuid: UUID,
    ) -> Result[errors.Error,
                tuple[domain.Item,
                      int,
                      list[models.User],
                      list[str],
                      models.MetainfoOld | None]]:
        """Execute."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.UPDATE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            total = await self.items_repo.count_all_children_of(item)
            can_see = await self.users_repo.get_users(
                uuids=item.permissions,
            )
            computed_tags = await self.items_repo.read_computed_tags(uuid)
            metainfo = await self.metainfo_repo.read_metainfo(item)

        return Success((item, total, can_see, computed_tags, metainfo))


class AppItemDeleteUseCase:
    """Use case for item deletion page."""

    def __init__(
            self,
            items_repo: storage_interfaces.AbsItemsRepo,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: models.User,
            uuid: UUID,
    ) -> Result[errors.Error, tuple[domain.Item, int]]:
        """Execute."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.DELETE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            total = await self.items_repo.count_all_children_of(item)

        return Success((item, total))
