"""Use cases that process browse requests from users."""

import time
from uuid import UUID

from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class ApiBrowseUseCase(BaseAPIUseCase):
    """Use case for browse."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        plan: models.Plan,
    ) -> tuple[float, list[models.Item], dict[int, models.User | None]]:
        """Perform search request."""
        start = time.perf_counter()

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)

            if user.is_anon and plan.direct:
                items = await self.mediator.browse.browse_direct_anon(conn, item, plan)
            elif user.is_anon and not plan.direct:
                items = await self.mediator.browse.browse_related_anon(conn, item, plan)
            elif user.is_not_anon and plan.direct:
                items = await self.mediator.browse.browse_direct_known(conn, user, item, plan)
            else:
                items = await self.mediator.browse.browse_related_known(conn, user, item, plan)

            users = await self.mediator.users.get_map(conn, items)

        duration = time.perf_counter() - start

        return duration, items, users
