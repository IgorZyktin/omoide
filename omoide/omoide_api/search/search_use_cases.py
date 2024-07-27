"""Use cases that process commands from users."""
import re
import time
from typing import Any
from typing import Literal

from omoide import custom_logging
from omoide import models
from omoide import utils
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


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

        repo = self.mediator.search_repo
        async with self.mediator.storage.transaction():
            if user.is_anon:
                variants = await repo.autocomplete_tag_anon(tag=tag,
                                                            limit=limit)
            else:
                variants = await repo.autocomplete_tag_known(user=user,
                                                             tag=tag,
                                                             limit=limit)
        return variants


class RecentUpdatesUseCase(BaseAPIUseCase):
    """Use case for getting recently updated items."""

    async def execute(
        self,
        user: models.User,
        last_seen: int,
        limit: int,
    ) -> tuple[list[models.Item], list[str | None]]:
        """Execute."""
        self.ensure_not_anon(user, operation='read recently updated items')

        async with self.mediator.storage.transaction():
            items = await self.mediator.browse_repo.get_recently_updated_items(
                user=user,
                last_seen=last_seen,
                limit=limit,
            )
            names = await self.mediator.browse_repo.get_parent_names(items)

        return items, names


class BaseSearchUseCase(BaseAPIUseCase):
    """Base class for search queries."""
    pattern = re.compile(r'(\s+\+\s+|\s+-\s+)')

    def parse_tags(self, query: str) -> tuple[set[str], set[str]]:
        """Split  user query into tags."""
        tags_include: set[str] = set()
        tags_exclude: set[str] = set()

        parts = self.pattern.split(query)
        clean_parts = [x.strip() for x in parts if x.strip()]

        if not clean_parts:
            return tags_include, tags_exclude

        if clean_parts[0] not in ('+', '-'):
            clean_parts.insert(0, '+')

        for operator, tag in utils.group_to_size(clean_parts):
            tag = str(tag).lower()
            if operator == '+':
                tags_include.add(tag)
            else:
                tags_exclude.add(tag)

        return tags_include, tags_exclude


class ApiSearchTotalUseCase(BaseSearchUseCase):
    """Use case for calculating total results of search."""

    async def execute(
        self,
        user: models.User,
        query: str,
        minimal_length: int,
        only_collections: bool,
    ) -> tuple[int, float]:
        """Perform search request."""
        total = 0
        duration = 0.0

        if len(query) < minimal_length:
            return total, duration

        start = time.perf_counter()
        tags_include, tags_exclude = self.parse_tags(query)

        async with self.mediator.storage.transaction():
            total = await self.mediator.search_repo.count(
                user=user,
                tags_include=tags_include,
                tags_exclude=tags_exclude,
                only_collections=only_collections,
            )

        duration = time.perf_counter() - start

        return total, duration


class ApiSearchUseCase(BaseSearchUseCase):
    """Use case for search."""

    async def execute(
        self,
        user: models.User,
        query: str,
        minimal_length: int,
        ordering: Literal['asc', 'desc', 'random'],
        only_collections: bool,
        last_seen: int,
        limit: int,
    ) -> tuple[float, list[models.Item], list[dict[str, Any]]]:
        """Perform search request."""
        duration = 0.0
        items: list[models.Item] = []
        extras: list[dict[str, Any]] = []

        if len(query) < minimal_length:
            return duration, items, extras

        start = time.perf_counter()
        tags_include, tags_exclude = self.parse_tags(query)

        async with self.mediator.storage.transaction():
            items = await self.mediator.search_repo.search(
                user,
                tags_include=tags_include,
                tags_exclude=tags_exclude,
                ordering=ordering,
                only_collections=only_collections,
                last_seen=last_seen,
                limit=limit,
            )
            names = await self.mediator.browse_repo.get_parent_names(items)

        duration = time.perf_counter() - start

        return duration, items, [{'parent_name': name} for name in names]
