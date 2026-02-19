"""Storage implementations."""

from omoide import models
from omoide.workers.converter.interfaces import AbsStorage


class PostgreSQLStorage(AbsStorage):
    """Storage in database."""

    def __init__(self, url: str, *, echo: bool) -> None:
        """Initialize instance."""
        self.url = url
        self.echo = echo

    def get_candidates(self, batch_size: int) -> list[int]:
        """Return candidates to operate on."""

    def lock(self, target_id: int) -> bool:
        """Lock specific object."""

    def load_model(self, target_id: int) -> models.InputMedia:
        """Load data from storage."""

    def mark_failed_and_release_lock(self, target_id: int, error: str) -> None:
        """Mark object as unprocessable."""

    def delete(self, target_id: int) -> None:
        """Delete specific object."""
