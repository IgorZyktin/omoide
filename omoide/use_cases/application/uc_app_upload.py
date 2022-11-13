# -*- coding: utf-8 -*-
"""Use case for upload.
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
    'AppUploadUseCase',
]


class AppUploadUseCase:
    """Use case for upload."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsReadRepository,
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
    ) -> Result[errors.Error, tuple[domain.Item, list[domain.User]]]:
        """Return preview model suitable for rendering."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.READ)
            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            users: list[UUID] = [UUID(x) for x in (item.permissions or [])]
            permissions = await self.users_repo.read_all_users(users)

        return Success((item, permissions))
