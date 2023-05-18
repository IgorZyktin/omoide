# -*- coding: utf-8 -*-
"""Use case for checking up updates.
"""
from typing import Optional

from omoide.application import app_models
from omoide.domain import errors
from omoide.domain import models
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_browse
from omoide.domain.special_types import Result
from omoide.domain.special_types import Success

__all__ = [
    'APIProfileNewUseCase',
]


class APIProfileNewUseCase:
    """Use case for checking up updates."""

    def __init__(
            self,
            browse_repo: in_rp_browse.AbsBrowseRepository,
    ) -> None:
        """Initialize instance."""
        self.browse_repo = browse_repo

    async def execute(
            self,
            user: models.User,
            aim: app_models.Aim,
    ) -> Result[errors.Error, tuple[list[models.Item], list[Optional[str]]]]:
        async with self.browse_repo.transaction():
            items = await self.browse_repo.get_recent_items(user, aim)
            names = await self.browse_repo.get_parents_names(items)

        return Success((items, names))
