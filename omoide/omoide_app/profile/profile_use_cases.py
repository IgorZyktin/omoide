"""Use case for user profile."""

from omoide import exceptions
from omoide import models
from omoide.omoide_app.common.common_use_cases import BaseAPPUseCase


class AppProfileUsageUseCase(BaseAPPUseCase):
    """Use case for user profile usage."""

    async def execute(
        self,
        user: models.User,
    ) -> tuple[models.SpaceUsage, int, int]:
        """Execute."""
        if user.is_anon:
            msg = 'Anon have no usage data'
            raise exceptions.AccessDeniedError(msg)

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
