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
        nested: bool,
        only_collections: bool,
        last_seen: int,
        limit: int,
    ) -> tuple[float, list[models.Item], list[dict[str, Any]]]:
        """Perform search request."""
        start = time.perf_counter()

        async with self.mediator.storage.transaction():
            repo = self.mediator.browse_repo

            if nested:
                if user.is_anon:
                    items = await repo.browse_nested_anon(
                        item_uuid=item_uuid,
                        order=order,
                        only_collections=only_collections,
                        last_seen=last_seen,
                        limit=limit,
                    )
                else:
                    items = await repo.browse_nested_known(
                        user=user,
                        item_uuid=item_uuid,
                        order=order,
                        only_collections=only_collections,
                        last_seen=last_seen,
                        limit=limit,
                    )
            else:
                if user.is_anon:
                    items = await repo.browse_all_anon(
                        item_uuid=item_uuid,
                        order=order,
                        only_collections=only_collections,
                        last_seen=last_seen,
                        limit=limit,
                    )
                else:
                    items = await repo.browse_all_known(
                        user=user,
                        item_uuid=item_uuid,
                        order=order,
                        only_collections=only_collections,
                        last_seen=last_seen,
                        limit=limit,
                    )

            names = await self.mediator.browse_repo.get_parent_names(items)

        duration = time.perf_counter() - start

        return duration, items, [{'parent_name': name} for name in names]
