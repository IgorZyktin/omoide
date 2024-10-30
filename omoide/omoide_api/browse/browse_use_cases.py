"""Use cases that process browse requests from users."""

import time
from typing import Any
from uuid import UUID

from omoide import const
from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class ApiBrowseUseCase(BaseAPIUseCase):
    """Use case for browse."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        direct: bool,
        collections: bool,
        last_seen: int,
        limit: int,
    ) -> tuple[float, list[models.Item], list[dict[str, Any]]]:
        """Perform search request."""
        start = time.perf_counter()

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)

            if direct:
                if user.is_anon:
                    items = await self.mediator.browse.browse_direct_anon(
                        conn=conn,
                        item=item,
                        order=order,
                        collections=collections,
                        last_seen=last_seen,
                        limit=limit,
                    )
                else:
                    items = await self.mediator.browse.browse_direct_known(
                        conn=conn,
                        user=user,
                        item=item,
                        order=order,
                        collections=collections,
                        last_seen=last_seen,
                        limit=limit,
                    )
            elif user.is_anon:
                items = await self.mediator.browse.browse_related_anon(
                    conn=conn,
                    item=item,
                    order=order,
                    collections=collections,
                    last_seen=last_seen,
                    limit=limit,
                )
            else:
                items = await self.mediator.browse.browse_related_known(
                    conn=conn,
                    user=user,
                    item=item,
                    order=order,
                    collections=collections,
                    last_seen=last_seen,
                    limit=limit,
                )

            names = await self.mediator.browse.get_parent_names(conn, items)

        duration = time.perf_counter() - start

        return duration, items, [{'parent_name': name} for name in names]
