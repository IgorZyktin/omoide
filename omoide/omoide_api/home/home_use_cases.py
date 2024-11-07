"""Use cases that process requests for home pages."""

from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class ApiHomeUseCase(BaseAPIUseCase):
    """Use case for getting home items."""

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Perform search request."""
        async with self.mediator.database.transaction() as conn:
            if user.is_anon:
                items = await self.mediator.search.get_home_items_for_anon(conn, plan)
            else:
                items = await self.mediator.search.get_home_items_for_known(conn, user, plan)

            users = await self.mediator.users.get_map(conn, items)

        return items, users
