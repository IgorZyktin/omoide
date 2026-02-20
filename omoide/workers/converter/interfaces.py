"""Application interfaces."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from omoide import models


class AbsDatabase(ABC):
    """Abstract storage."""

    @abstractmethod
    def connect(self) -> None:
        """Connect to database."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from database."""

    @abstractmethod
    def get_media_candidates(
        self,
        batch_size: int,
        content_types: Sequence[str],
    ) -> list[int]:
        """Return candidates to operate on."""

    @abstractmethod
    def lock(self, target_id: int, name: str) -> bool:
        """Lock specific object."""

    @abstractmethod
    def load_media(self, target_id: int) -> models.InputMedia:
        """Load data from storage."""

    @abstractmethod
    def save_media(self, model: models.InputMedia, media_type: str) -> None:
        """Save data to storage."""

    @abstractmethod
    def mark_failed_and_release_lock(self, target_id: int, error: str) -> None:
        """Mark object as unprocessable."""

    @abstractmethod
    def delete_media(self, target_id: int) -> None:
        """Delete specific object."""
