"""Repository that perform operations on tags."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsTagsRepo(Generic[ConnectionT], abc.ABC):
    """Repository that perform operations on tags."""

    @abc.abstractmethod
    async def get_known_tags_anon(
        self,
        conn: ConnectionT,
        batch_size: int,
    ) -> dict[str, int]:
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
    async def get_known_tags_user(
        self,
        conn: ConnectionT,
        user: models.User,
        batch_size: int,
    ) -> dict[str, int]:
        """Return known tags for specific user."""

    @abc.abstractmethod
    async def drop_known_tags_user(
        self,
        conn: ConnectionT,
        user: models.User,
    ) -> int:
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
    async def get_computed_tags(
        self,
        conn: ConnectionT,
        item: models.Item,
    ) -> set[str]:
        """Return computed tags for given item."""

    @abc.abstractmethod
    async def save_computed_tags(
        self,
        conn: ConnectionT,
        item: models.Item,
        tags: set[str],
    ) -> None:
        """Save computed tags for given item."""
