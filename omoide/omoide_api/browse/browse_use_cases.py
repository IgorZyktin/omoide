"""Use cases that process browse requests from users."""

import time
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
    ) -> tuple[float, list[models.Item], dict[int, models.User | None]]:
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

            users = await self.mediator.users.get_map(conn, items)

        duration = time.perf_counter() - start

        return duration, items, users
