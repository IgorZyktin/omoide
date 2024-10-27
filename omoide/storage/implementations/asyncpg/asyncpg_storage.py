"""Base storage class."""

from contextlib import asynccontextmanager
from typing import Any

from omoide.storage.interfaces.abs_storage import AbsStorage


class AsyncpgStorage(AbsStorage):
    """Base storage class."""

    def __init__(self, db: Any) -> None:
        """Initialize instance."""
        self.db = db

    @asynccontextmanager
    async def transaction(self) -> Any:
        """Start transaction."""
        async with self.db.transaction():
            yield self.db
