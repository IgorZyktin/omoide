"""Abstract base object storage."""

import abc
from typing import TypedDict

from omoide import const
from omoide import models


class SoftDeleteEntry(TypedDict):
    """DTO for deletion."""

    media_type: str
    operation_id: int


class AbsObjectStorage(abc.ABC):
    """Abstract base object storage."""

    @abc.abstractmethod
    async def save(
        self,
        item: models.Item,
        media_type: const.MEDIA_TYPE,
        binary_content: bytes,
        ext: str,
    ) -> None:
        """Save object of specific content type."""

    @abc.abstractmethod
    async def soft_delete(
        self,
        requested_by: models.User,
        owner: models.User,
        item: models.Item,
    ) -> list[SoftDeleteEntry]:
        """Mark all objects as deleted."""

    @abc.abstractmethod
    async def copy_all_objects(
        self,
        requested_by: models.User,
        owner: models.User,
        source_item: models.Item,
        target_item: models.Item,
    ) -> list[const.MEDIA_TYPE]:
        """Copy all objects from one item to another."""
