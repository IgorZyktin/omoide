"""Use case for items."""
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide import models
from omoide.domain import actions
from omoide.domain import errors
from omoide import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage import interfaces as storage_interfaces

__all__ = [
    'AppItemCreateUseCase',
    'AppItemUpdateUseCase',
    'AppItemDeleteUseCase',
]


class AppItemCreateUseCase:
    """Use case for item creation page."""

    def __init__(
            self,
            users_repo: storage_interfaces.AbsUsersRepo,
            items_repo: storage_interfaces.AbsItemsRepo,
    ) -> None:
        """Initialize instance."""
        self.users_repo = users_repo
        self.items_repo = items_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: models.User,
            parent_uuid: Optional[UUID],
    ) -> Result[errors.Error, tuple[domain.Item, list[models.User]]]:
        """Business logic."""
        async with self.items_repo.transaction():
            if parent_uuid is None:
                root_item = await self.items_repo.get_root_item(user)
                parent_uuid = root_item.uuid

            if parent_uuid is None:
                return Failure(errors.ItemDoesNotExist(uuid=parent_uuid))

            error = await policy.is_restricted(user, parent_uuid,
                                               actions.Item.CREATE)
            if error:
                return Failure(error)

            parent = await self.items_repo.read_item(parent_uuid)

            if parent is None:
                return Failure(errors.ItemDoesNotExist(uuid=parent_uuid))

            can_see = await self.users_repo.read_filtered_users(
                *parent.permissions
            )

        return Success((parent, can_see))


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
                      Optional[models.MetainfoOld]]]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.UPDATE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            total = await self.items_repo.count_all_children_of(item)
            can_see = await self.users_repo.read_filtered_users(
                *item.permissions
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
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.DELETE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            total = await self.items_repo.count_all_children_of(item)

        return Success((item, total))
