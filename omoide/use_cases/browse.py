# -*- coding: utf-8 -*-
"""Use case for browse.
"""
from omoide.domain import auth, browse, common
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
    ) -> browse.Result:
        """Return browse model suitable for rendering."""
        async with self._repo.transaction():
            access = await self._repo.check_access(user, item_uuid)

            if access.is_not_given:
                location = common.Location.empty()
                total_items = 0
                items = []
            else:
                location = await self._repo.get_location(item_uuid)
                items = await self._repo.get_nested_items(item_uuid, query)
                total_items = await self._repo.count_nested_items(item_uuid)

        total_pages = int(total_items / (query.items_per_page or 1))

        return browse.Result(
            access=access,
            location=location,
            page=query.page,
            total_items=total_items,
            total_pages=total_pages,
            items=items,
        )
