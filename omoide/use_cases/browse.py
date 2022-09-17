# -*- coding: utf-8 -*-
"""Use case for browse.
"""
from typing import NamedTuple
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces, exceptions

__all__ = [
    'AppBrowseUseCase',
    'APIBrowseUseCase',
]


class BrowseResult(NamedTuple):
    """DTO for current use case."""
    item: domain.Item
    location: domain.SimpleLocation | domain.Location
    total_items: int
    total_pages: int
    items: list
    details: domain.Details
    paginated: bool = True


class AppBrowseUseCase:
    """Use case for browse (application)."""

    def __init__(self, repo: interfaces.AbsBrowseRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            aim: domain.Aim,
            details: domain.Details,
    ) -> BrowseResult:
        """Return browse model suitable for rendering."""
        # TODO(i.zyktin): need heavy refactoring
        async with self._repo.transaction():
            await self._repo.assert_has_access(user, uuid,
                                               only_for_owner=False)

            item = await self._repo.read_item(uuid)
            if item is None:
                raise exceptions.NotFound(f'Item {uuid} does not exist')

            owner = await self._repo.get_user(item.owner_uuid)
            if owner is None:
                raise exceptions.NotFound(
                    f'User {item.owner_uuid} does not exist')

            if aim.paged:
                return await self.go_browse_paginated(user, owner,
                                                      item, details)
            else:
                return await self.go_browse_dynamic(user, owner, item, details)

    async def go_browse_paginated(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
            details: domain.Details,
    ) -> BrowseResult:
        """Browse with pagination."""
        location = await self._repo.get_location(user, item.uuid, details)

        # TODO(i.zyktin): must consider owner when gathering children
        assert owner

        if user.is_anon():
            items = await self._repo.get_children(item.uuid, details)
            total_items = await self._repo.count_items(item.uuid)
        else:
            items = await self._repo.get_specific_children(
                user=user,
                uuid=item.uuid,
                details=details,
            )
            total_items = await self._repo.count_specific_items(
                user=user,
                item_uuid=item.uuid,
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
        location = await self._repo.get_simple_location(user, owner, item)
        return BrowseResult(
            item=item,
            total_items=-1,
            total_pages=-1,
            items=[],
            details=details,
            location=location,
            paginated=False,
        )


class APIBrowseUseCase:
    """Use case for browse (api)."""

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        access = await self._repo.check_access(user, uuid)

        if access.does_not_exist or access.is_not_given:
            return []

        async with self._repo.transaction():
            if aim.nested:
                items = await self._repo.simple_find_items_to_browse(
                    user=user,
                    uuid=uuid,
                    aim=aim,
                )

            else:
                items = await self._repo.complex_find_items_to_browse(
                    user=user,
                    uuid=uuid,
                    aim=aim,
                )

        return items
