"""Repository that perform operations on tags."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsTagsRepo(Generic[ConnectionT], abc.ABC):
    """Repository that perform operations on tags."""

    @abc.abstractmethod
    async def get_known_tags_anon(self, conn: ConnectionT) -> dict[str, int]:
        """Return known tags for anon."""

    @abc.abstractmethod
    async def drop_known_tags_anon(self, conn: ConnectionT) -> int:
        """Drop all known tags for anon user."""

    @abc.abstractmethod
    async def insert_known_tags_anon(
        self,
        conn: ConnectionT,
        tags: dict[str, int],
        batch_size: int,
    ) -> None:
        """Insert given tags for anon user."""

    @abc.abstractmethod
    async def increment_known_tags_user(
        self,
        conn: ConnectionT,
        user: models.User,
        tags: set[str],
    ) -> None:
        """Increase counter for given tags."""

    @abc.abstractmethod
    async def increment_known_tags_anon(self, conn: ConnectionT, tags: set[str]) -> None:
        """Increase counter for given tags."""

    @abc.abstractmethod
    async def decrement_known_tags_user(
        self,
        conn: ConnectionT,
        user: models.User,
        tags: set[str],
    ) -> None:
        """Decrease counter for given tags."""

    @abc.abstractmethod
    async def decrement_known_tags_anon(self, conn: ConnectionT, tags: set[str]) -> None:
        """Decrease counter for given tags."""

    @abc.abstractmethod
    async def get_known_tags_user(self, conn: ConnectionT, user: models.User) -> dict[str, int]:
        """Return known tags for specific user."""

    @abc.abstractmethod
    async def drop_known_tags_user(self, conn: ConnectionT, user: models.User) -> int:
        """Drop all known tags for specific user."""

    @abc.abstractmethod
    async def insert_known_tags_user(
        self,
        conn: ConnectionT,
        user: models.User,
        tags: dict[str, int],
        batch_size: int,
    ) -> None:
        """Insert given tags for specific user."""

    @abc.abstractmethod
    async def get_computed_tags(self, conn: ConnectionT, item: models.Item) -> set[str]:
        """Return computed tags for given item."""

    @abc.abstractmethod
    async def save_computed_tags(
        self,
        conn: ConnectionT,
        item: models.Item,
        tags: set[str],
    ) -> None:
        """Save computed tags for given item."""

    @abc.abstractmethod
    async def count_all_tags_anon(self, conn: ConnectionT) -> dict[str, int]:
        """Return counters for known tags (anon user)."""

    @abc.abstractmethod
    async def count_all_tags_known(self, conn: ConnectionT, user: models.User) -> dict[str, int]:
        """Return counters for known tags (known user)."""

    @abc.abstractmethod
    async def autocomplete_tag_anon(
        self,
        conn: ConnectionT,
        tag: str,
        limit: int,
    ) -> list[str]:
        """Autocomplete tag for anon user."""

    @abc.abstractmethod
    async def autocomplete_tag_known(
        self,
        conn: ConnectionT,
        user: models.User,
        tag: str,
        limit: int,
    ) -> list[str]:
        """Autocomplete tag for known user."""
