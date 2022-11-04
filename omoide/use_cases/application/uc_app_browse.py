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

__all__ = [
    'BrowseResult',
    'AppBrowseUseCase',
]

from omoide.infra.special_types import Success


class BrowseResult(NamedTuple):
    """DTO for current use case."""
    item: domain.Item
    location: domain.SimpleLocation | domain.Location | None
    total_items: int
    total_pages: int
    items: list
    details: domain.Details
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
            details: domain.Details,
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
                result = await self.go_browse_paginated(
                    user, owner, item, details)

            else:
                result = await self.go_browse_dynamic(
                    user, owner, item, details)

            return Success(result)

    async def go_browse_paginated(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
            details: domain.Details,
    ) -> BrowseResult:
        """Browse with pagination."""
        location = await self.browse_repo.get_location(
            user=user,
            uuid=item.uuid,
            details=details,
            users_repo=self.users_repo,
        )

        # TODO(i.zyktin): must consider owner when gathering children
        assert owner

        if user.is_anon():
            items = await self.browse_repo.get_children(
                uuid=item.uuid,
                details=details,
            )
            total_items = await self.browse_repo.count_items(
                uuid=item.uuid,
            )

        else:
            items = await self.browse_repo.get_specific_children(
                user=user,
                uuid=item.uuid,
                details=details,
            )
            total_items = await self.browse_repo.count_specific_items(
                user=user,
                uuid=item.uuid,
            )

        return BrowseResult(
            item=item,
            total_items=total_items,
            total_pages=details.calc_total_pages(total_items),
            items=items,
            details=details,
            location=location,
            paginated=True,
        )

    async def go_browse_dynamic(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
            details: domain.Details,
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
            details=details,
            location=location,
            paginated=False,
        )
