# -*- coding: utf-8 -*-
"""Database tools for worker.
"""
from omoide.daemons.common.base_db import BaseDatabase


class Database(BaseDatabase):
    """Wrapper on SQL commands for worker."""

    def get_media_ids(
            self,
            formula: dict[str, dict[str, bool]],
            limit: int,
    ) -> list[int]:
        """Extract media resources to save."""
        # TODO
        return []

    def get_filesystem_operations(
            self,
            limit: int,
    ) -> list[int]:
        """Extract operations to process."""
        # TODO
        return []

    def drop_media(
            self,
            replication_formula: dict[str, dict[str, bool]],
    ) -> int:
        """Delete fully downloaded media rows, return total amount."""
        # TODO
        return 0
