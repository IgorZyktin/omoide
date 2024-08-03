"""Abstract base object storage."""
import abc

from omoide import const
from omoide import models


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
        """Save object."""

    @abc.abstractmethod
    async def delete(self) -> None:
        """Delete object."""

    @abc.abstractmethod
    async def copy(self) -> None:
        """Copy object."""
