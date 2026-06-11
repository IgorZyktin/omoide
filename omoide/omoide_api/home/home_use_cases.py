"""Use cases that process requests for home pages."""

from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase


class ApiHomeUseCase:
    """Use case for getting home items."""

    def __init__(
        self,
        database: AbsDatabase,
        search: db_interfaces.AbsSearchRepo,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.search = search
        self.users = users

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Perform search request."""
        async with self.database.transaction() as conn:
            if user.is_anon:
                items = await self.search.get_home_items_for_anon(conn, plan)
            else:
                items = await self.search.get_home_items_for_known(conn, user, plan)

            users = await self.users.get_map(conn, items)

        return items, users
