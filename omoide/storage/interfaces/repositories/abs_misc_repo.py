"""Repository that performs various operations on different objects."""

import abc
from collections.abc import Collection
from datetime import datetime
from typing import Any
from uuid import UUID

from omoide import models


class AbsMiscRepo(abc.ABC):
    """Repository that performs various operations on different objects."""

    @abc.abstractmethod
    async def get_computed_tags(self, item: models.Item) -> set[str]:
        """Get computed tags for this item."""

    @abc.abstractmethod
    async def update_computed_tags(
        self,
        item: models.Item,
        parent_computed_tags: set[str],
    ) -> set[str]:
        """Update computed tags for this item."""

    @abc.abstractmethod
    async def update_known_tags(
        self,
        users: Collection[models.User],
        tags_added: Collection[str],
        tags_deleted: Collection[str],
    ) -> None:
        """Update counters for known tags."""

    @abc.abstractmethod
    async def incr_known_tags_anon(
        self,
        tags: Collection[str],
    ) -> None:
        """Increment tag counter."""

    @abc.abstractmethod
    async def incr_known_tags_known(
        self,
        user: models.User,
        tags: Collection[str],
    ) -> None:
        """Increment tag counter."""

    @abc.abstractmethod
    async def decr_known_tags_anon(
        self,
        tags: Collection[str],
    ) -> None:
        """Decrement tag counter."""

    @abc.abstractmethod
    async def decr_known_tags_known(
        self,
        user: models.User,
        tags: Collection[str],
    ) -> None:
        """Decrement tag counter."""

    @abc.abstractmethod
    async def drop_unused_known_tags_anon(self) -> None:
        """Drop tags with counter less of equal to 0."""

    @abc.abstractmethod
    async def drop_unused_known_tags_known(self, user: models.User) -> None:
        """Drop tags with counter less of equal to 0."""

    @abc.abstractmethod
    async def start_long_job(
        self,
        name: str,
        user_uuid: UUID,
        target_uuid: UUID | None,
        added: Collection[str],
        deleted: Collection[str],
        started: datetime,
        extras: dict[str, Any],
    ) -> int:
        """Start long job."""

    @abc.abstractmethod
    async def finish_long_job(
        self,
        id: int,
        status: str,
        duration: float,
        operations: int,
        error: str,
    ) -> None:
        """Finish long job."""

    @abc.abstractmethod
    async def create_serial_operation(
        self,
        name: str,
        extras: dict[str, Any],
    ) -> int:
        """Create serial operation."""
