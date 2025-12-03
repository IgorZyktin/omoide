"""Use cases that process requests for home pages."""

from omoide import models
from omoide.database import interfaces as db_interfaces


class ApiHomeUseCase:
    """Use case for getting home items."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        users_repo: db_interfaces.AbsUsersRepo,
        search_repo: db_interfaces.AbsSearchRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users_repo = users_repo
        self.search_repo = search_repo

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Perform search request."""
        async with self.database.transaction() as conn:
            if user.is_anon:
                items = await self.search_repo.get_home_items_for_anon(conn, plan)
            else:
                items = await self.search_repo.get_home_items_for_known(conn, user, plan)

            users = await self.users_repo.get_map(conn, items)

        return items, users
