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
    'AppItemsDownloadUseCase',
]


class AppItemCreateUseCase:
    """Use case for item creation page."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            users_repo: interfaces.AbsUsersReadRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.users_repo = users_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            parent_uuid: Optional[UUID],
    ) -> Result[errors.Error, tuple[domain.Item, list[domain.User]]]:
        """Business logic."""
        async with self.items_repo.transaction():
            if parent_uuid is None:
                parent_uuid = user.root_item

            if parent_uuid is None:
                return Failure(errors.ItemDoesNotExist(uuid=parent_uuid))

            error = await policy.is_restricted(user, parent_uuid,
                                               actions.Item.CREATE)
            if error:
                return Failure(error)

            parent = await self.items_repo.read_item(parent_uuid)

            if parent is None:
                return Failure(errors.ItemDoesNotExist(uuid=parent_uuid))

            can_see = await self.users_repo.read_all_users(parent.permissions)

        return Success((parent, can_see))


class AppItemUpdateUseCase:
    """Use case for item modification page."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            users_repo: interfaces.AbsUsersReadRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.users_repo = users_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, tuple[domain.Item, int, list[domain.User]]]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.UPDATE)

            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            total = await self.items_repo.count_all_children(uuid)
            can_see = await self.users_repo.read_all_users(item.permissions)

        return Success((item, total, can_see))


class AppItemDeleteUseCase:
    """Use case for item deletion page."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
    ) -> None:
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


class AppItemsDownloadUseCase:
    """Use case for item download page."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsReadRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, list[tuple[str, domain.Item]]]:
        """Business logic."""
        numerated_items: list[tuple[str, domain.Item]] = []

        async with self.items_repo.transaction():
            # TODO: read_children_safe -> read_children
            items = await self.items_repo.read_children_safe(
                user, uuid, ignore_collections=True)
            total = len(items)

            if total:
                digits = len(str(total))
                number = 1
                template = f'{{:0{digits}d}}'
                for item in items:
                    numerated_items.append((template.format(number), item))
                    number += 1

        return Success(numerated_items)
