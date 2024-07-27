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
    async def update_computed_tags(
        self,
        user: models.User,
        item: domain.Item,
    ) -> None:
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
    async def drop_unused_known_tags(
        self,
        users: Collection[models.User],
        public_users: set[UUID],
    ) -> None:
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
