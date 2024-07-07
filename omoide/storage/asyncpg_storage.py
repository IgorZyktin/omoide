"""Base storage class."""
from typing import Any

from omoide.domain.interfaces.in_storage.in_repositories.in_rp_base import (
    AbsStorage
)


class AsyncpgStorage(AbsStorage):
    """Base storage class."""

    def __init__(self, db: Any) -> None:
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:
        """Start transaction."""
        return self.db.transaction()
