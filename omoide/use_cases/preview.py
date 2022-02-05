# -*- coding: utf-8 -*-
"""Use case for preview.
"""
from omoide.domain import auth, preview, common
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
            details: common.Details,
    ) -> preview.Result:
        """Return preview model suitable for rendering."""
        async with self._repo.transaction():
            access = await self._repo.check_access(user, item_uuid)

            if access.is_not_given:
                item = None
                neighbours = []
                location = common.Location.empty()
            else:
                item = await self._repo.get_preview_item(item_uuid)
                neighbours = await self._repo.get_neighbours(item_uuid)
                # FIXME
                location = await self._repo.get_location(item_uuid, details)

        return preview.Result(
            access=access,
            item=item,
            neighbours=neighbours,
            location=location,
        )
