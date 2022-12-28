# -*- coding: utf-8 -*-
"""Use case for user profile quotas.
"""
from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'AppProfileQuotasUseCase',
]


class AppProfileQuotasUseCase:
    """Use case for user profile quotas."""

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
    ) -> Result[errors.Error, tuple[domain.SpaceUsage, int, int]]:
        """Return amount of items that correspond to query (not items)."""
        if user.is_anon() or user.uuid is None:
            return Failure(errors.AuthenticationRequired())

        if user.root_item is None:
            return Success((domain.SpaceUsage.empty(user.uuid), 0, 0))

        async with self.users_repo.transaction():
            root = await self.items_repo.read_item(user.root_item)
            if root is None:
                return Success((domain.SpaceUsage.empty(user.uuid), 0, 0))

            size = await self.users_repo.calc_total_space_used_by(user)
            total_items = await self.items_repo \
                .count_items_by_owner(user)
            total_collections = await self.items_repo \
                .count_items_by_owner(user, only_collections=True)

        return Success((size, total_items, total_collections))
