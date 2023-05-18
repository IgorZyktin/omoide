# -*- coding: utf-8 -*-
"""Use case for preview.
"""
from uuid import UUID

from omoide import domain
from omoide.application import app_models
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import models
from omoide.domain.interfaces.in_infra import in_policy
from omoide.domain.interfaces.in_storage.in_repositories import \
    in_rp_items_read
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_metainfo
from omoide.domain.interfaces.in_storage.in_repositories import \
    in_rp_preview
from omoide.domain.interfaces.in_storage.in_repositories import \
    in_rp_users_read
from omoide.domain.special_types import Failure
from omoide.domain.special_types import Result
from omoide.domain.special_types import Success

__all__ = [
    'AppPreviewUseCase',
]


class AppPreviewUseCase:
    """Use case for preview."""

    def __init__(
            self,
            preview_repo: in_rp_preview.AbsPreviewRepository,
            users_repo: in_rp_users_read.AbsUsersReadRepository,
            items_repo: in_rp_items_read.AbsItemsReadRepository,
            meta_repo: in_rp_metainfo.AbsMetainfoRepository,
    ) -> None:
        """Initialize instance."""
        self.preview_repo = preview_repo
        self.users_repo = users_repo
        self.items_repo = items_repo
        self.meta_repo = meta_repo

    async def execute(
            self,
            policy: in_policy.AbsPolicy,
            user: models.User,
            uuid: UUID,
            aim: app_models.Aim,
    ) -> Result[errors.Error, app_models.SingleResult]:
        """Return preview model suitable for rendering."""
        async with self.preview_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.READ)

            if error:
                return Failure(error)

            location = await self.preview_repo.get_location(
                user=user,
                uuid=uuid,
                aim=aim,
                users_repo=self.users_repo,
            )

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            metainfo = await self.meta_repo.read_metainfo(uuid)

            if metainfo is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            neighbours = await self.preview_repo.get_neighbours(
                user=user,
                uuid=uuid,
            )

            result = domain.SingleResult(
                item=item,
                metainfo=metainfo,
                aim=aim,
                location=location,
                neighbours=neighbours,
            )

        return Success(result)
