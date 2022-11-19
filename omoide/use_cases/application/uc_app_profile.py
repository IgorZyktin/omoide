# -*- coding: utf-8 -*-
"""Use case for user profile.
"""
from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'AppProfileUseCase',
]


class AppProfileUseCase:
    """Use case for user profile."""

    def __init__(
            self,
            users_repo: interfaces.AbsUsersReadRepository,
            items_repo: interfaces.AbsItemsReadRepository,
    ) -> None:
        """Initialize instance."""
        self.users_repo = users_repo
        self.items_repo = items_repo

    async def execute(
            self,
            user: domain.User,
    ) -> Result[errors.Error, tuple[domain.SpaceUsage, int]]:
        """Return amount of items that correspond to query (not items)."""
        if user.is_anon() or user.uuid is None:
            return Failure(errors.AuthenticationRequired())

        if user.root_item is None:
            return Success((domain.SpaceUsage.empty(user.uuid), 0))

        async with self.users_repo.transaction():
            root = await self.items_repo.read_item(user.root_item)
            if root is None:
                return Success((domain.SpaceUsage.empty(user.uuid), 0))

            size = await self.users_repo.calc_total_space_used(user, root)
            total = await self.items_repo.count_items_by_owner(user.uuid)

        return Success((size, total))
