# -*- coding: utf-8 -*-
"""Use case for preview.
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
    'AppPreviewUseCase',
]


class AppPreviewUseCase:
    """Use case for preview."""

    def __init__(
            self,
            preview_repo: interfaces.AbsPreviewRepository,
            users_repo: interfaces.AbsUsersReadRepository,
            items_repo: interfaces.AbsItemsReadRepository,
    ) -> None:
        """Initialize instance."""
        self.preview_repo = preview_repo
        self.users_repo = users_repo
        self.items_repo = items_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            details: domain.Details,
    ) -> Result[errors.Error, domain.SingleResult]:
        """Return preview model suitable for rendering."""
        async with self.preview_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.READ)
            if error:
                return Failure(error)

            location = await self.preview_repo.get_location(
                user=user,
                uuid=uuid,
                details=details,
                users_repo=self.users_repo,
            )

            item = await self.items_repo.read_item(uuid)

            if user.is_anon():
                neighbours = await self.preview_repo.get_neighbours(
                    uuid=uuid,
                )
            else:
                neighbours = await self.preview_repo.get_specific_neighbours(
                    user=user,
                    uuid=uuid,
                )

            result = domain.SingleResult(
                item=item,
                details=details,
                location=location,
                neighbours=neighbours,
            )

        return Success(result)
