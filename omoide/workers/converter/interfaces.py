"""Application interfaces."""

from abc import ABC

from omoide import models


class AbsStorage(ABC):
    """Abstract storage."""

    def get_candidates(self, batch_size: int) -> list[int]:
        """Return candidates to operate on."""

    def lock(self, target_id: int, name: str) -> bool:
        """Lock specific object."""

    def load_model(self, target_id: int) -> models.InputMedia:
        """Load data from storage."""

    def mark_failed_and_release_lock(self, target_id: int, error: str) -> None:
        """Mark object as unprocessable."""

    def delete(self, target_id: int) -> None:
        """Delete specific object."""
