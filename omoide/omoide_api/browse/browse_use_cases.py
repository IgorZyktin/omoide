"""Use cases that process browse requests from users."""

import time
from typing import NamedTuple
from uuid import UUID

from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase


class BrowseResult(NamedTuple):
    """Descendants of a browsed item with users referenced and elapsed time."""

    duration: float
    items: list[models.Item]
    users_map: dict[int, models.User | None]


class ApiBrowseUseCase:
    """Use case for browse."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        browse: db_interfaces.AbsBrowseRepo,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items
        self.browse = browse
        self.users = users

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        plan: models.Plan,
    ) -> BrowseResult:
        """Perform search request."""
        start = time.perf_counter()

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)

            if user.is_anon and plan.direct:
                items = await self.browse.browse_direct_anon(conn, item, plan)
            elif user.is_anon and not plan.direct:
                items = await self.browse.browse_related_anon(conn, item, plan)
            elif user.is_not_anon and plan.direct:
                items = await self.browse.browse_direct_known(conn, user, item, plan)
            else:
                items = await self.browse.browse_related_known(conn, user, item, plan)

            users_map = await self.users.get_map(conn, items)

        duration = time.perf_counter() - start

        return BrowseResult(duration=duration, items=items, users_map=users_map)
