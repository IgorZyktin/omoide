"""Use cases that process browse requests from users."""
import time
from typing import Any
from typing import Literal
from uuid import UUID

from omoide import models
from omoide import const
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class ApiBrowseUseCase(BaseAPIUseCase):
    """Use case for browse."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
        order: const.ORDER_TYPE,
        only_collections: bool,
        last_seen: int,
        limit: int,
    ) -> tuple[float, list[models.Item], list[dict[str, Any]]]:
        """Perform search request."""
        start = time.perf_counter()

        async with self.mediator.storage.transaction():
            repo = self.mediator.browse_repo

            if only_collections:
                items = await repo.simple_browse(
                    user=user,
                    item_uuid=item_uuid,
                    order=order,
                    last_seen=last_seen,
                    limit=limit,
                )

            else:
                items = await repo.complex_browse(
                    user=user,
                    item_uuid=item_uuid,
                    order=order,
                    last_seen=last_seen,
                    limit=limit,
                )

            names = await self.mediator.browse_repo.get_parent_names(items)

        duration = time.perf_counter() - start

        return duration, items, [{'parent_name': name} for name in names]
