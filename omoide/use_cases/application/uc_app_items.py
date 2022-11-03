# -*- coding: utf-8 -*-
"""Use case for items.
"""
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'AppItemCreateUseCase',
    'AppItemUpdateUseCase',
    'AppItemDeleteUseCase',
]


class AppItemCreateUseCase:
    """Use case for item creation page."""

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
            parent_uuid: Optional[UUID],
    ) -> Result[errors.Error,
                tuple[domain.Item, list[domain.User]]]:
        """Business logic."""
        async with self.items_repo.transaction():
            if parent_uuid is None:
                parent_uuid = user.root_item

            error = await policy.is_restricted(user, parent_uuid,
                                               actions.Item.CREATE)
            if error:
                return Failure(error)

            parent = await self.items_repo.read_item(parent_uuid)

            if parent is None:
                return Failure(errors.ItemDoesNotExist(uuid=parent_uuid))

            users: list[UUID] = [UUID(x) for x in (parent.permissions or [])]
            permissions = await self.users_repo.read_all_users(users)

        return Success((parent, permissions))


class AppItemUpdateUseCase:
    """Use case for item modification page."""

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
            users: list[str | UUID] = [
                str(x) for x in (item.permissions or [])
            ]
            permissions = await self.users_repo.read_all_users(users)

        return Success((item, total, permissions))


class AppItemDeleteUseCase:
    """Use item deletion page."""

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
