# -*- coding: utf-8 -*-
"""Database tools for worker.
"""
from typing import Optional

import sqlalchemy as sa

from omoide.daemons.common.base_db import BaseDatabase
from omoide.storage.database import models


class Database(BaseDatabase):
    """Wrapper on SQL commands for worker."""

    def get_media_ids(
            self,
            formula: dict[str, bool],
            limit: int,
            max_attempts: int = 5,
    ) -> list[int]:
        """Extract media resources to save."""
        stmt = sa.select(
            models.Media.id
        ).where(
            models.Media.processed_at != None,  # noqa
            ~models.Media.replication.contains(formula),
            models.Media.attempts < max_attempts,
        ).order_by(
            models.Media.id
        ).limit(
            limit
        )
        with self.engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return list(response)

    def select_media(
            self,
            media_id: int,
    ) -> Optional[models.Media]:
        """Select Media for update."""
        result = self.session.query(
            models.Media
        ).with_for_update(
            skip_locked=True
        ).filter_by(
            id=media_id
        ).first()
        return result

    def get_filesystem_operations(
            self,
            limit: int,
            max_attempts: int = 5,
    ) -> list[int]:
        """Extract operations to process."""
        stmt = sa.select(
            models.FilesystemOperation.id
        ).where(
            models.FilesystemOperation.processed_at != None,  # noqa
            models.FilesystemOperation.status == 'init',
            models.FilesystemOperation.attempts < max_attempts,
        ).order_by(
            models.FilesystemOperation.id
        ).limit(
            limit
        )
        with self.engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return list(response)

    def drop_media(
            self,
            formula: dict[str, bool],
    ) -> int:
        """Delete fully downloaded media rows, return total amount."""
        stmt = sa.delete(
            models.Media
        ).where(
            models.Media.replication.contains(formula),
            models.Media.replication.has_all(formula),
        )

        with self.engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return int(response.rowcount)
