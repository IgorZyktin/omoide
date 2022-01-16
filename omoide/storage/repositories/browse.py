# -*- coding: utf-8 -*-
"""Browse repository.
"""
from omoide.domain import preview, auth, browse
from omoide.domain.interfaces import database
from omoide.storage.repositories import browse_sql


class BrowseRepository(database.AbsBrowseRepository):
    """Repository that performs all browse queries."""
    _q_access = browse_sql.CHECK_ACCESS
    _q_items = browse_sql.GET_NESTED_ITEMS

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    async def get_nested_items(
            self,
            user: auth.User,
            item_uuid: str,
            query: browse.Query,
    ) -> tuple[browse.Result, browse.AccessStatus]:
        """Load all children with all required fields."""
        async with self.db.transaction():
            status = await self._check_access(user, item_uuid)

            if status.is_not_given:
                result = browse.Result(
                    page=-1,
                    total_items=-1,
                    total_pages=-1,
                    items=[],
                )
            else:
                result = await self._get_nested_items(item_uuid, query)

        return result, status

    async def _check_access(
            self,
            user: auth.User,
            item_uuid: str,
    ) -> preview.AccessStatus:
        """Check access to the item."""
        response = await self.db.fetch_one(
            query=self._q_access,
            values={'user_uuid': user.uuid, 'item_uuid': item_uuid}
        )

        if response is None:
            return preview.AccessStatus(
                exists=False,
                is_public=False,
                is_given=False,
            )

        return preview.AccessStatus(
            exists=True,
            is_public=bool(response['is_public']),
            is_given=bool(response['is_given']),
        )

    async def _get_nested_items(
            self,
            item_uuid: str,
            query: browse.Query,
    ) -> browse.Result:
        """Load search result."""
        response = await self.db.fetch_all(
            query=self._q_items,
            values={
                'item_uuid': item_uuid,
                'limit': query.items_per_page,
                'offset': (query.page - 1) * query.items_per_page,
            }
        )

        if response is None:
            return browse.Result(
                page=-1,
                total_items=-1,
                total_pages=-1,
                items=[],
            )

        items = []
        total_items = 0
        for row in response:
            total_items, item = self._cast_item(row)
            items.append(item)

        total_pages = int(total_items / (query.items_per_page or 1))

        return browse.Result(
            page=min(query.page, total_pages),
            total_items=total_items,
            total_pages=total_pages,
            items=items,
        )

    @staticmethod
    def _cast_item(raw_item) -> tuple[int, browse.SimpleItem]:
        """Convert from db format to required model."""

        def as_str(key: str) -> str | None:
            """Extract optional."""
            value = raw_item[key]
            if value is None:
                return None
            return str(value)

        return raw_item['total_items'], browse.SimpleItem(
            owner_uuid=as_str('owner_uuid'),
            uuid=as_str('uuid'),
            is_collection=raw_item['is_collection'],
            name=raw_item['name'],
            ext=raw_item['ext'],
        )
