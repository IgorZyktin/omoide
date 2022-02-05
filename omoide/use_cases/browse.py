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
            query: common.Query,
    ) -> browse.Result:
        """Return browse model suitable for rendering."""
        async with self._repo.transaction():
            access = await self._repo.check_access(user, item_uuid)

            if access.is_not_given:
                location = common.Location.empty()
                items = []
                total_items = 0
            else:
                location = await self._repo.get_location(item_uuid,
                                                         query.items_per_page)
                items = await self._repo.get_children(item_uuid, query)
                total_items = await self._repo.count_items(item_uuid)

        return browse.Result(
            access=access,
            location=location,
            page=query.page,
            total_items=total_items,
            total_pages=query.calc_total_pages(total_items),
            items=items,
        )
