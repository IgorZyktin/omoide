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

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self.items_repo = repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, None]:
        """Business logic."""
        error = None
        if error:
            return Failure(error)
        return Success(None)


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
    ) -> Result[errors.Error, tuple[int, domain.Item]]:
        """Business logic."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.DELETE)

            if error:
                return Failure(error)

            total = await self.items_repo.count_all_children(uuid)
            item = await self.items_repo.read_item(uuid)

        return Success((item, total))
