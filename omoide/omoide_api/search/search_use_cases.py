"""Use cases that process search requests from users."""

import time

from omoide import models
from omoide import utils
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase


class AutocompleteUseCase:
    """Use case for suggesting tag autocomplete."""

    def __init__(
        self,
        database: AbsDatabase,
        tags: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.tags = tags

    async def execute(
        self,
        user: models.User,
        tag: str,
        minimal_length: int,
        limit: int,
    ) -> list[str]:
        """Execute."""
        if len(tag) < minimal_length:
            return []

        async with self.database.transaction() as conn:
            if user.is_anon:
                variants = await self.tags.autocomplete_tag_anon(conn, tag, limit)
            else:
                variants = await self.tags.autocomplete_tag_user(conn, user, tag, limit)

        return [variant for variant in variants if not utils.looks_like_uuid(variant)]


class RecentUpdatesUseCase:
    """Use case for getting recently updated items."""

    def __init__(
        self,
        database: AbsDatabase,
        browse: db_interfaces.AbsBrowseRepo,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.browse = browse
        self.users = users

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        async with self.database.transaction() as conn:
            if user.is_anon:
                items = await self.browse.get_recently_updated_items_anon(conn, plan)
            else:
                items = await self.browse.get_recently_updated_items_known(conn, user, plan)
            users = await self.users.get_map(conn, items)
        return items, users


class ApiSearchTotalUseCase:
    """Use case for calculating total results of search."""

    def __init__(
        self,
        database: AbsDatabase,
        search: db_interfaces.AbsSearchRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.search = search

    async def execute(self, user: models.User, plan: models.Plan) -> tuple[int, float]:
        """Execute."""
        start = time.perf_counter()

        async with self.database.transaction() as conn:
            total = await self.search.count(conn, user, plan)

        duration = time.perf_counter() - start

        return total, duration


class ApiSearchUseCase:
    """Use case for search."""

    def __init__(
        self,
        database: AbsDatabase,
        search: db_interfaces.AbsSearchRepo,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.search = search
        self.users = users

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[float, list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        start = time.perf_counter()

        async with self.database.transaction() as conn:
            items = await self.search.search(conn, user, plan)
            users = await self.users.get_map(conn, items)

        duration = time.perf_counter() - start

        return duration, items, users
