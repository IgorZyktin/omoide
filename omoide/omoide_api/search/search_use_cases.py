"""Use cases that process search requests from users."""

import time
from typing import NamedTuple

from omoide import models
from omoide import utils
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase


class ItemsResult(NamedTuple):
    """Multi-item lookup result with users referenced by their permissions."""

    items: list[models.Item]
    users_map: dict[int, models.User | None]


class SearchTotalResult(NamedTuple):
    """Total matches for a search query plus how long the count took."""

    total: int
    duration: float


class SearchResult(NamedTuple):
    """Search hit list with users referenced and how long it took to run."""

    duration: float
    items: list[models.Item]
    users_map: dict[int, models.User | None]


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

        return [
            variant.replace(' - ', ' \\- ')
            for variant in variants
            if not utils.looks_like_uuid(variant)
        ]


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
    ) -> ItemsResult:
        """Execute."""
        async with self.database.transaction() as conn:
            if user.is_anon:
                items = await self.browse.get_recently_updated_items_anon(conn, plan)
            else:
                items = await self.browse.get_recently_updated_items_known(conn, user, plan)
            users_map = await self.users.get_map(conn, items)
        return ItemsResult(items=items, users_map=users_map)


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

    async def execute(self, user: models.User, plan: models.Plan) -> SearchTotalResult:
        """Execute."""
        start = time.perf_counter()

        async with self.database.transaction() as conn:
            total = await self.search.count(conn, user, plan)

        duration = time.perf_counter() - start

        return SearchTotalResult(total=total, duration=duration)


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
    ) -> SearchResult:
        """Execute."""
        start = time.perf_counter()

        async with self.database.transaction() as conn:
            items = await self.search.search(conn, user, plan)
            users_map = await self.users.get_map(conn, items)

        duration = time.perf_counter() - start

        return SearchResult(duration=duration, items=items, users_map=users_map)
