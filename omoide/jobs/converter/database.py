# -*- coding: utf-8 -*-
"""Database operations for converter job.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide.storage.database.models import RawMedia


def get_uuids_to_process(engine: Engine, limit: int) -> list[UUID]:
    """Return UUIDs of all unprocessed items from raw media table."""
    query = sqlalchemy.select(
        RawMedia.item_uuid
    ).where(
        RawMedia.status == 'init'
    ).order_by(
        RawMedia.id
    )

    if limit > 0:
        query = query.limit(limit)

    with engine.begin() as conn:
        response = conn.execute(query)
        uuids = response.fetchall()

    return [uuid for uuid, in uuids]


def claim(engine: Engine, uuid: UUID) -> bool:
    """Return True if we could get lock to this target."""
    command = sqlalchemy.update(
        RawMedia
    ).where(
        RawMedia.item_uuid == uuid,
        RawMedia.status == 'init',
    ).values(
        status='work'
    )

    with engine.begin() as conn:
        response = conn.execute(command)
        return response.rowcount == 1


def get_raw_media_instance(session: Session, uuid: UUID) -> Optional[RawMedia]:
    """Return instance from database."""
    return session.query(
        RawMedia
    ).where(
        RawMedia.item_uuid == uuid
    ).first()
