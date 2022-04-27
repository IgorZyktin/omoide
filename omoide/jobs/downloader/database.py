# -*- coding: utf-8 -*-
"""Database operations for downloader job.
"""
from sqlalchemy.orm import Session

from omoide.storage.database.models import Media


def get_media_records(session: Session, limit: int) -> list[Media]:
    """Return some media records to save."""
    query = session.query(Media).where(Media.status == 'init')

    if limit > 0:
        query = query.limit(limit)

    return query.all()
