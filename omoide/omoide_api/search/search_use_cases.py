"""Use cases that process search requests from users."""

import time

from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class AutocompleteUseCase(BaseAPIUseCase):
    """Use case for suggesting tag autocomplete."""

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

        async with self.mediator.database.transaction() as conn:
            if user.is_anon:
                variants = await self.mediator.tags.autocomplete_tag_anon(conn, tag, limit)
            else:
                variants = await self.mediator.tags.autocomplete_tag_known(conn, user, tag, limit)
        return variants


class RecentUpdatesUseCase(BaseAPIUseCase):
    """Use case for getting recently updated items."""

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to='read recently updated items')

        async with self.mediator.database.transaction() as conn:
            items = await self.mediator.browse.get_recently_updated_items(conn, user, plan)
            users = await self.mediator.users.get_map(conn, items)

        return items, users


class BaseSearchUseCase(BaseAPIUseCase):
    """Base class for search queries."""


class ApiSearchTotalUseCase(BaseSearchUseCase):
    """Use case for calculating total results of search."""

    async def execute(self, user: models.User, plan: models.Plan) -> tuple[int, float]:
        """Execute."""
        start = time.perf_counter()

        async with self.mediator.database.transaction() as conn:
            total = await self.mediator.search.count(conn, user, plan)

        duration = time.perf_counter() - start

        return total, duration


class ApiSearchUseCase(BaseSearchUseCase):
    """Use case for search."""

    async def execute(
        self,
        user: models.User,
        plan: models.Plan,
    ) -> tuple[float, list[models.Item], dict[int, models.User | None]]:
        """Execute."""
        start = time.perf_counter()

        async with self.mediator.database.transaction() as conn:
            items = await self.mediator.search.search(conn, user, plan)
            users = await self.mediator.users.get_map(conn, items)

        duration = time.perf_counter() - start

        return duration, items, users
