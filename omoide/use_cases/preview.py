# -*- coding: utf-8 -*-
"""Use case for preview.
"""
from omoide.domain import auth, preview
from omoide.domain.interfaces import database


class PreviewUseCase:
    """Use case for preview."""

    def __init__(self, repo: database.AbsPreviewRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> tuple[preview.Item, list[str], preview.AccessStatus]:
        """Return preview model suitable for rendering."""
        return await self._repo.get_item_or_empty(user, item_uuid)
