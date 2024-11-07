"""Use case for user profile."""

from omoide import models
from omoide.omoide_app.common.common_use_cases import BaseAPPUseCase


class AppProfileUsageUseCase(BaseAPPUseCase):
    """Use case for user profile usage."""

    async def execute(
        self,
        user: models.User,
    ) -> tuple[models.SpaceUsage, int, int]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            size = await self.mediator.users.calc_total_space_used_by(conn, user)
            total_items = await self.mediator.users.count_items_by_owner(conn, user)
            total_collections = await self.mediator.users.count_items_by_owner(
                conn=conn,
                user=user,
                collections=True,
            )

        return size, total_items, total_collections


class AppProfileTagsUseCase(BaseAPPUseCase):
    """Use case for user profile tags."""

    async def execute(self, user: models.User) -> dict[str, int]:
        """Return tags with their counters."""
        async with self.mediator.database.transaction() as conn:
            known_tags = await self.mediator.tags.count_all_tags_known(conn, user)
        return known_tags


class AppProfileDuplicatesUseCase(BaseAPPUseCase):
    """Use case for duplicated items search."""

    async def execute(
        self,
        user: models.User,
        limit: int,
    ) -> list[models.Duplication]:
        """Return groups of items with same hash."""
        async with self.mediator.database.transaction() as conn:
            duplicates = await self.mediator.items.get_duplicates(conn, user, limit)
        return duplicates
