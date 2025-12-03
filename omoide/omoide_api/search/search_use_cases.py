"""Use cases that process search requests from users."""

import time

from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class AutocompleteUseCase:
    """Use case for suggesting tag autocomplete."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        tags_repo: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.tags_repo = tags_repo

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
                variants = await self.tags_repo.autocomplete_tag_anon(conn, tag, limit)
            else:
                variants = await self.tags_repo.autocomplete_tag_user(conn, user, tag, limit)
        return variants


class RecentUpdatesUseCase:
    """Use case for getting recently updated items."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        users_repo: db_interfaces.AbsUsersRepo,
        browse_repo: db_interfaces.AbsBrowseRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users_repo = users_repo
        self.browse_repo = browse_repo

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        async with self.database.transaction() as conn:
            if user.is_anon:
                items = await self.browse_repo.get_recently_updated_items_anon(conn, plan)
            else:
                items = await self.browse_repo.get_recently_updated_items_known(conn, user, plan)
            users = await self.users_repo.get_map(conn, items)

        return items, users


class BaseSearchUseCase(BaseAPIUseCase):
    """Base class for search queries."""


class ApiSearchTotalUseCase:
    """Use case for calculating total results of search."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        search_repo: db_interfaces.AbsSearchRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.search_repo = search_repo

    async def execute(self, user: models.User, plan: models.Plan) -> tuple[int, float]:
        """Execute."""
        start = time.perf_counter()

        async with self.database.transaction() as conn:
            total = await self.search_repo.count(conn, user, plan)

        duration = time.perf_counter() - start

        return total, duration


class ApiSearchUseCase:
    """Use case for search."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        users_repo: db_interfaces.AbsUsersRepo,
        search_repo: db_interfaces.AbsSearchRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users_repo = users_repo
        self.search_repo = search_repo

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[float, list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        start = time.perf_counter()

        async with self.database.transaction() as conn:
            items = await self.search_repo.search(conn, user, plan)
            users = await self.users_repo.get_map(conn, items)

        duration = time.perf_counter() - start

        return duration, items, users
