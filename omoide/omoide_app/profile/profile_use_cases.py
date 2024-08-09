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
        async with self.mediator.storage.transaction():
            size = await self.mediator.users_repo.calc_total_space_used_by(
                user=user,
            )
            repo = self.mediator.items_repo
            total_items = await repo.count_items_by_owner(user)
            total_collections = await repo.count_items_by_owner(
                user=user,
                collections=True,
            )

        return size, total_items, total_collections


class AppProfileTagsUseCase(BaseAPPUseCase):
    """Use case for user profile tags."""

    async def execute(self, user: models.User) -> dict[str, int]:
        """Return tags with their counters."""
        async with self.mediator.storage.transaction():
            known_tags = await self.mediator.search_repo.count_all_tags_known(
                user=user,
            )
        return known_tags
