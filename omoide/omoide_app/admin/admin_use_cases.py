"""Use cases for admins."""

from omoide import models
from omoide.database.interfaces import AbsDatabase

from omoide.database import interfaces as db_interfaces
from omoide.domain import ensure


class ShowResourceUsageUseCase:
    """Use case for disk usage display."""

    def __init__(
        self,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users = users
        self.meta = meta

    async def execute(self, user: models.User) -> models.ResourceUsageStats:
        """Execute."""
        ensure.admin(user, 'Only admins can see resource usage')
        resource_usage: list[models.ResourceUsage] = []

        async with self.database.transaction() as conn:
            users = await self.users.select(conn)
            for user in users:
                items = await self.users.count_items_by_owner(conn, user)

                if items <= 1:
                    continue

                disk = await self.meta.get_total_disk_usage(conn, user)
                collections = await self.users.count_items_by_owner(
                    conn, user, collections=True
                )
                usage = models.ResourceUsage(
                    user=user,
                    total_items=items,
                    total_collections=collections,
                    disk_usage=disk,
                )
                resource_usage.append(usage)

        resource_usage.sort(key=lambda x: x.total_items, reverse=True)
        return models.ResourceUsageStats(
            users=resource_usage,
        )
