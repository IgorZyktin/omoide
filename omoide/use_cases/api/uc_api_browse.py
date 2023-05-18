# -*- coding: utf-8 -*-
"""Use case for browse.
"""
from typing import Optional
from uuid import UUID

import omoide.domain.models
from omoide.application import app_models
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import models
from omoide.domain.interfaces.in_infra import in_policy
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_browse
from omoide.domain.special_types import Failure
from omoide.domain.special_types import Result
from omoide.domain.special_types import Success

__all__ = [
    'APIBrowseUseCase',
]


class APIBrowseUseCase:
    """Use case for browse (api)."""

    def __init__(
            self,
            browse_repo: in_rp_browse.AbsBrowseRepository,
    ) -> None:
        """Initialize instance."""
        self.browse_repo = browse_repo

    async def execute(
            self,
            policy: in_policy.AbsPolicy,
            user: omoide.domain.models.User,
            uuid: UUID,
            aim: app_models.Aim,
    ) -> Result[errors.Error, tuple[list[models.Item], list[Optional[str]]]]:
        async with self.browse_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.READ)

            if error:
                return Failure(error)

            if aim.nested:
                items = await self.browse_repo.simple_find_items_to_browse(
                    user=user,
                    uuid=uuid,
                    aim=aim,
                )

            else:
                items = await self.browse_repo.complex_find_items_to_browse(
                    user=user,
                    uuid=uuid,
                    aim=aim,
                )

            names = await self.browse_repo.get_parents_names(items)

        return Success((items, names))
