"""Use cases that process browse requests from users."""

import time
from uuid import UUID

from omoide import models
from omoide.database import interfaces as db_interfaces


class ApiBrowseUseCase:
    """Use case for browse."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        users_repo: db_interfaces.AbsUsersRepo,
        items_repo: db_interfaces.AbsItemsRepo,
        browse_repo: db_interfaces.AbsBrowseRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users_repo = users_repo
        self.items_repo = items_repo
        self.browse_repo = browse_repo

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        plan: models.Plan,
    ) -> tuple[float, list[models.Item], dict[int, models.User | None]]:
        """Perform search request."""
        start = time.perf_counter()

        async with self.database.transaction() as conn:
            item = await self.items_repo.get_by_uuid(conn, item_uuid)

            if user.is_anon and plan.direct:
                items = await self.browse_repo.browse_direct_anon(conn, item, plan)
            elif user.is_anon and not plan.direct:
                items = await self.browse_repo.browse_related_anon(conn, item, plan)
            elif user.is_not_anon and plan.direct:
                items = await self.browse_repo.browse_direct_known(conn, user, item, plan)
            else:
                items = await self.browse_repo.browse_related_known(conn, user, item, plan)

            users = await self.users_repo.get_map(conn, items)

        duration = time.perf_counter() - start

        return duration, items, users
