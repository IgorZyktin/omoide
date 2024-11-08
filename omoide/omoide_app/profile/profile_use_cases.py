"""Use case for user profile."""
from uuid import UUID

from omoide import models
from omoide import utils
from omoide.omoide_app.common.common_use_cases import BaseAPPUseCase


class AppProfileUsageUseCase(BaseAPPUseCase):
    """Use case that returns info about total space usage by current user."""

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
    """Use case that return all known tags for current user."""

    async def execute(self, user: models.User) -> dict[str, int]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            known_tags = await self.mediator.tags.get_known_tags_user(conn, user)
            clean_tags = {
                tag: counter for tag, counter in known_tags.items() if not utils.is_valid_uuid(tag)
            }
        return clean_tags


class AppProfileDuplicatesUseCase(BaseAPPUseCase):
    """Use case that returns duplicated items for current user."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID | None,
        limit: int,
    ) -> tuple[models.Item | None, list[models.Duplicate]]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            if item_uuid is not None:
                item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            else:
                item = None

            duplicates = await self.mediator.items.get_duplicates(conn, user, item, limit)

        return item, duplicates
