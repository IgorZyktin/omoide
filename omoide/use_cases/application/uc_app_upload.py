# -*- coding: utf-8 -*-
"""Use case for upload.
"""
from uuid import UUID

import omoide.domain.models
from omoide import domain
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.domain import models
from omoide.domain.interfaces.in_infra import in_policy
from omoide.domain.interfaces.in_storage.in_repositories import \
    in_rp_items_read
from omoide.domain.interfaces.in_storage.in_repositories import \
    in_rp_users_read
from omoide.domain.special_types import Failure
from omoide.domain.special_types import Result
from omoide.domain.special_types import Success

__all__ = [
    'AppUploadUseCase',
]


class AppUploadUseCase:
    """Use case for upload."""

    def __init__(
            self,
            users_repo: in_rp_users_read.AbsUsersReadRepository,
            items_repo: in_rp_items_read.AbsItemsReadRepository,
    ) -> None:
        """Initialize instance."""
        self.users_repo = users_repo
        self.items_repo = items_repo

    async def execute(
            self,
            policy: in_policy.AbsPolicy,
            user: omoide.domain.models.User,
            uuid: UUID,
    ) -> Result[errors.Error, tuple[models.Item, list[
        omoide.domain.models.User]]]:
        """Return preview model suitable for rendering."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.UPDATE)
            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            can_see = await self.users_repo.read_all_users(*item.permissions)

        return Success((item, can_see))
