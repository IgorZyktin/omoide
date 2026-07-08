"""Use case for user profile."""

from typing import NamedTuple
from uuid import UUID

import python_utilz as pu

from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.domain import ensure


class ProfileUsage(NamedTuple):
    """Disk usage stats shown on the profile usage page."""

    size: models.SpaceUsage
    total_items: int
    total_collections: int


class ProfileDuplicates(NamedTuple):
    """Duplicate listing shown on the profile duplicates page."""

    item: models.Item | None
    duplicates: list[models.Duplicate]


class AppProfileUsageUseCase:
    """Use case that returns info about total space usage by current user."""

    def __init__(
        self,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users = users

    async def execute(
        self,
        user: models.User,
    ) -> ProfileUsage:
        """Execute."""
        ensure.registered(user, 'Anonymous users have no resource usage')

        async with self.database.transaction() as conn:
            size = await self.users.calc_total_space_used_by(conn, user)
            total_items = await self.users.count_items_by_owner(conn, user)
            total_collections = await self.users.count_items_by_owner(
                conn=conn,
                user=user,
                collections=True,
            )

        return ProfileUsage(
            size=size,
            total_items=total_items,
            total_collections=total_collections,
        )


class AppProfileTagsUseCase:
    """Use case that return all known tags for current user."""

    def __init__(
        self,
        database: AbsDatabase,
        tags: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.tags = tags

    async def execute(self, user: models.User) -> dict[str, int]:
        """Execute."""
        ensure.registered(user, 'Anonymous users have no tags page')

        async with self.database.transaction() as conn:
            known_tags = await self.tags.get_known_tags_user(conn, user)
            clean_tags = {
                tag: counter
                for tag, counter in known_tags.items()
                if not pu.is_valid_uuid(tag) and counter > 0
            }
        return clean_tags


class AppProfileDuplicatesUseCase:
    """Use case that returns duplicated items for current user."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items

    async def execute(
        self,
        user: models.User,
        item_uuid: str | None,
        limit: int,
    ) -> ProfileDuplicates:
        """Execute."""
        ensure.registered(user, 'Anonymous users have no duplicates page')

        async with self.database.transaction() as conn:
            if item_uuid is not None and pu.is_valid_uuid(item_uuid):
                item = await self.items.get_by_uuid(conn, UUID(item_uuid))
            else:
                item = None

            duplicates = await self.items.get_duplicates(conn, user, item, limit)

        return ProfileDuplicates(item=item, duplicates=duplicates)
