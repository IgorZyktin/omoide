# -*- coding: utf-8 -*-
"""Database operations for downloader job.
"""
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide.storage.database.models import Media


def claim(engine: Engine, media: Media) -> bool:
    """Return True if we could get lock to this target."""
    command = sqlalchemy.update(
        Media
    ).where(
        Media.item_uuid == media.item_uuid,
        Media.type == media.type,
        Media.status == 'init',
    ).values(
        status='work'
    )

    with engine.begin() as conn:
        response = conn.execute(command)
        return response.rowcount == 1


def get_media_records(session: Session, limit: int) -> list[Media]:
    """Return some media records to save."""
    query = session.query(Media).where(Media.status == 'init')

    if limit > 0:
        query = query.limit(limit)

    return query.all()
