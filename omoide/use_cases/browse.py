# -*- coding: utf-8 -*-
"""Use case for browse.
"""
from omoide.domain import auth, browse
from omoide.domain.interfaces import database


class BrowseUseCase:
    """Use case for browse."""

    def __init__(self, repo: database.AbsBrowseRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: auth.User,
            item_uuid: str,
            query: browse.Query,
    ) -> tuple[browse.Result, browse.AccessStatus]:
        """Return browse model suitable for rendering."""
        return await self._repo.get_nested_items(user, item_uuid, query)
