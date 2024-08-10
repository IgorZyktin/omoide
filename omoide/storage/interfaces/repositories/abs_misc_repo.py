"""Repository that performs various operations on different objects."""

import abc
from collections.abc import Collection
from datetime import datetime
from typing import Any
from uuid import UUID

from omoide import domain  # FIXME - use models instead
from omoide import models


class AbsMiscRepo(abc.ABC):
    """Repository that performs various operations on different objects."""

    @abc.abstractmethod
    async def read_children_to_download(
        self,
        user: models.User,
        item: domain.Item,
    ) -> list[dict[str, UUID | str | int]]:
        """Return some components of the given item children with metainfo."""

    @abc.abstractmethod
    async def get_computed_tags(self, item: models.Item) -> set[str]:
        """Get computed tags for this item."""

    @abc.abstractmethod
    async def update_computed_tags(self, item: models.Item) -> set[str]:
        """Update computed tags for this item."""

    @abc.abstractmethod
    async def replace_computed_tags(
        self,
        item: models.Item,
        tags: set[str]
    ) -> None:
        """Replace all computed tags for this item."""

    @abc.abstractmethod
    async def update_known_tags(
        self,
        users: Collection[models.User],
        tags_added: Collection[str],
        tags_deleted: Collection[str],
    ) -> None:
        """Update counters for known tags."""

    @abc.abstractmethod
    async def increment_known_tags_for_anon_user(
        self,
        tags: Collection[str],
    ) -> None:
        """Increment tag counter."""

    @abc.abstractmethod
    async def increment_known_tags_for_known_user(
        self,
        user: models.User,
        tags: Collection[str],
    ) -> None:
        """Increment tag counter."""

    @abc.abstractmethod
    async def decrement_known_tags_for_anon_user(
        self,
        tags: Collection[str],
    ) -> None:
        """Decrement tag counter."""

    async def decrement_known_tags_for_known_user(
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
    async def calculate_known_tags_anon(
        self,
        batch_size: int,
    ) -> dict[str, int]:
        """Recalculate all known tags for anon."""

    @abc.abstractmethod
    async def calculate_known_tags_known(
        self,
        user: models.User,
        batch_size: int,
    ) -> dict[str, int]:
        """Recalculate all known tags for known user."""

    @abc.abstractmethod
    async def insert_known_tags_anon(
        self,
        known_tags: dict[str, int],
    ) -> None:
        """Insert batch of known tags."""

    @abc.abstractmethod
    async def insert_known_tags_known(
        self,
        user: models.User,
        known_tags: dict[str, int],
    ) -> None:
        """Insert batch of known tags."""

    @abc.abstractmethod
    async def drop_known_tags_anon(self) -> None:
        """Clean all known tags for anon."""

    @abc.abstractmethod
    async def drop_known_tags_known(self, user: models.User) -> None:
        """Clean all known tags for known user."""

    @abc.abstractmethod
    async def save_md5_signature(
        self,
        item: models.Item,
        signature: str
    ) -> None:
        """Create signature record."""

    @abc.abstractmethod
    async def save_cr32_signature(
        self,
        item: models.Item,
        signature: str
    ) -> None:
        """Create signature record."""

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
