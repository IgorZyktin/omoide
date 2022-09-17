# -*- coding: utf-8 -*-
"""Use case for items.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'AppItemUpdateUseCase',
    'AppItemDeleteUseCase',
]


class AppItemUpdateUseCase:
    """Use case for item modification."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsRepository,
            users_repo: interfaces.AbsUsersRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.users_repo = users_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error,
                tuple[domain.Item, int, list[domain.User]]]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.UPDATE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            total = await self.items_repo.count_all_children(uuid)
            permissions = await self.users_repo.read_all_users(
                item.permissions)

        return Success((item, total, permissions))


class AppItemDeleteUseCase:
    """Use case for deleting an item."""

    def __init__(self, items_repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self.items_repo = items_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
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

            total = await self.items_repo.count_all_children(uuid)

        return Success((item, total))