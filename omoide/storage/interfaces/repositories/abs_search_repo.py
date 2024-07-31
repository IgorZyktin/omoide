"""Repository that performs all search queries."""
import abc
from typing import Literal

from omoide import models


class AbsSearchRepository(abc.ABC):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def count(
        self,
        user: models.User,
        tags_include: set[str],
        tags_exclude: set[str],
        only_collections: bool,
    ) -> int:
        """Return total amount of items relevant to this search query."""

    @abc.abstractmethod
    async def search(
        self,
        user: models.User,
        tags_include: set[str],
        tags_exclude: set[str],
        only_collections: bool,
        order: Literal['asc', 'desc', 'random'],
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return matching items for search query."""

    @abc.abstractmethod
    async def get_home_items_for_anon(
        self,
        user: models.User,
        only_collections: bool,
        order: Literal['asc', 'desc', 'random'],
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return home items for anon."""

    @abc.abstractmethod
    async def get_home_items_for_known(
        self,
        user: models.User,
        only_collections: bool,
        order: Literal['asc', 'desc', 'random'],
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return home items for known user."""

    @abc.abstractmethod
    async def count_all_tags_anon(self) -> dict[str, int]:
        """Return counters for known tags (anon user)."""

    @abc.abstractmethod
    async def count_all_tags_known(self, user: models.User) -> dict[str, int]:
        """Return counters for known tags (known user)."""

    @abc.abstractmethod
    async def autocomplete_tag_anon(self, tag: str, limit: int) -> list[str]:
        """Autocomplete tag for anon user."""

    @abc.abstractmethod
    async def autocomplete_tag_known(
        self,
        user: models.User,
        tag: str,
        limit: int,
    ) -> list[str]:
        """Autocomplete tag for known user."""
