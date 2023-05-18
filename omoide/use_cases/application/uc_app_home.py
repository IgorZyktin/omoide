# -*- coding: utf-8 -*-
"""Use case for home page.
"""
from typing import Optional

import omoide.domain.models
from omoide.application import app_models
from omoide.domain import models
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_browse
from omoide.domain.special_types import Success

__all__ = [
    'AppHomeUseCase',
]


class AppHomeUseCase:
    """Use case for home page."""

    def __init__(self, browse_repo: in_rp_browse.AbsBrowseRepository) -> None:
        """Initialize instance."""
        self.browse_repo = browse_repo

    async def execute(
            self,
            user: omoide.domain.models.User,
            aim: app_models.Aim,
    ) -> Success[tuple[list[models.Item], list[Optional[str]]]]:
        """Perform request for home directory."""
        async with self.browse_repo.transaction():
            items = await self.browse_repo.simple_find_items_to_browse(
                user=user,
                uuid=None,
                aim=aim,
            )
            names = await self.browse_repo.get_parents_names(items)

        return Success((items, names))
