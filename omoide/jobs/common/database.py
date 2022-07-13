# -*- coding: utf-8 -*-
"""Database operations for all jobs.
"""
import sys
from typing import Callable, Iterator, Any, Optional
from uuid import UUID

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide.jobs.job_config import JobConfig
from omoide.storage.database import models


def get_candidates(
        config: JobConfig,
        engine: Engine,
        getter: Callable[[Engine,
                          int,
                          Optional[tuple[UUID, str]]], list[tuple[UUID, str]]],
) -> Iterator[list[Any]]:
    """Load packs of primary keys to process."""
    limit = sys.maxsize if config.limit == -1 else config.limit
    last_seen = None
    processed = 0

    while processed < limit:
        batch_size = min(config.batch_size, limit - processed)
        candidates = getter(engine, batch_size, last_seen)

        if not candidates:
            break

        yield candidates
        processed += len(candidates)
        last_seen = candidates[-1]


_LOCATION_CACHE: dict[UUID, str] = {}


def get_cached_location_for_an_item(session: Session, item_uuid: UUID) -> str:
    """Fast way of getting item location."""
    location = _LOCATION_CACHE.get(item_uuid)

    if location is None:
        location = get_location_for_an_item(session, item_uuid)
        _LOCATION_CACHE[item_uuid] = location

    return location


def get_location_for_an_item(session: Session, item_uuid: UUID) -> str:
    """Get human-readable location of an item."""
    current_uuid = item_uuid
    segments = []
    done_steps = 0
    max_steps = 100

    while current_uuid:
        done_steps += 1
        item = session.query(models.Item).get(current_uuid)
        current_uuid = item.parent_uuid
        segments.append(item.name or str(item.uuid))

        if done_steps > max_steps:
            # TODO: replace it with proper logger call
            print('got into loop during parent search')
            break

    if not segments:
        return '???'

    return '/'.join(reversed(segments))


def claim(
        engine: Engine,
        uuid: UUID,
        media_type: str,
) -> bool:
    """Return True if we could get lock to this target."""
    command = sqlalchemy.update(
        models.Media
    ).where(
        models.Media.item_uuid == uuid,
        models.Media.media_type == media_type,
        models.Media.status == 'init',
    ).values(
        status='work'
    )

    with engine.begin() as conn:
        response = conn.execute(command)
        return response.rowcount == 1
