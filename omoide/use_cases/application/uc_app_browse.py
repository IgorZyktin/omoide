# -*- coding: utf-8 -*-
"""Use case for browse.
"""
from typing import NamedTuple
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'BrowseResult',
    'AppBrowseUseCase',
]


class BrowseResult(NamedTuple):
    """DTO for current use case."""
    item: domain.Item
    location: domain.SimpleLocation | domain.Location | None
    total_items: int
    total_pages: int
    items: list
    aim: domain.Aim
    paginated: bool = True


class AppBrowseUseCase:
    """Use case for browse (application)."""

    def __init__(
            self,
            browse_repo: interfaces.AbsBrowseRepository,
            users_repo: interfaces.AbsUsersReadRepository,
            items_repo: interfaces.AbsItemsReadRepository,
    ) -> None:
        """Initialize instance."""
        self.browse_repo = browse_repo
        self.items_repo = items_repo
        self.users_repo = users_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            aim: domain.Aim,
    ) -> Result[errors.Error, BrowseResult]:
        """Return browse model suitable for rendering."""
        async with self.browse_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.READ)
            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            owner = await self.users_repo.read_user(item.owner_uuid)
            if owner is None:
                return Failure(errors.UserDoesNotExist(uuid=item.owner_uuid))

            if aim.paged:
                result = await self.go_browse_paginated(user, item, aim)

            else:
                result = await self.go_browse_dynamic(
                    user, owner, item, aim)

            return Success(result)

    async def go_browse_paginated(
            self,
            user: domain.User,
            item: domain.Item,
            aim: domain.Aim,
    ) -> BrowseResult:
        """Browse with pagination."""
        location = await self.browse_repo.get_location(
            user=user,
            uuid=item.uuid,
            aim=aim,
            users_repo=self.users_repo,
        )

        items = await self.browse_repo.get_children(
            user=user,
            uuid=item.uuid,
            aim=aim,
        )

        total_items = await self.browse_repo.count_children(
            user=user,
            uuid=item.uuid,
        )

        return BrowseResult(
            item=item,
            total_items=total_items,
            total_pages=aim.calc_total_pages(total_items),
            items=items,
            aim=aim,
            location=location,
            paginated=True,
        )

    async def go_browse_dynamic(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
            aim: domain.Aim,
    ) -> BrowseResult:
        """Browse without pagination."""
        location = await self.items_repo.get_simple_location(
            user=user,
            owner=owner,
            item=item,
        )

        return BrowseResult(
            item=item,
            total_items=-1,
            total_pages=-1,
            items=[],
            aim=aim,
            location=location,
            paginated=False,
        )
