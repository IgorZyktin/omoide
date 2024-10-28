"""Use cases that process requests for home pages."""

import time
from typing import Any

from omoide import const
from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class ApiHomeUseCase(BaseAPIUseCase):
    """Use case for getting home items."""

    async def execute(
        self,
        user: models.User,
        order: const.ORDER_TYPE,
        collections: bool,
        direct: bool,
        last_seen: int,
        limit: int,
    ) -> tuple[float, list[models.Item], list[dict[str, Any]]]:
        """Perform search request."""
        start = time.perf_counter()

        async with self.mediator.database.transaction() as conn:
            if user.is_anon:
                items = await self.mediator.search.get_home_items_for_anon(
                    conn=conn,
                    order=order,
                    collections=collections,
                    direct=direct,
                    last_seen=last_seen,
                    limit=limit,
                )

            else:
                items = await self.mediator.search.get_home_items_for_known(
                    conn=conn,
                    user=user,
                    order=order,
                    collections=collections,
                    direct=direct,
                    last_seen=last_seen,
                    limit=limit,
                )

            names = await self.mediator.browse.get_parent_names(conn, items)

        duration = time.perf_counter() - start

        return duration, items, [{'parent_name': name} for name in names]
