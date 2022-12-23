# -*- coding: utf-8 -*-
"""Utils for commands.
"""
import contextlib
import time
from typing import Callable
from typing import Iterator
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from omoide.commands.common.base_db import BaseDatabase
from omoide.storage.database import models

TPL = str | None | Callable[[], str | None]


@contextlib.contextmanager
def timing(
        callback: Callable = print,
        start_template: TPL = lambda: None,
        end_template: TPL = 'Finished in {delta:0.2f} seconds',
) -> Iterator[None]:
    """Create engine and dispose it after completion."""

    def _get_template(template: TPL) -> str | None:
        if template is None or not template:
            return None

        if isinstance(template, str):
            return template

        return template() or None

    def _maybe_print(template: str | None, **kwargs) -> None:
        if template:
            callback(template.format(**kwargs))

    full_start_template = _get_template(start_template)
    full_end_template = _get_template(end_template)

    started_at = time.perf_counter()
    try:
        _maybe_print(full_start_template)
        yield
    finally:
        ended_at = time.perf_counter()
        delta = ended_at - started_at
        _maybe_print(full_end_template, delta=delta)


def get_users(database: BaseDatabase) -> list[models.User]:
    """Get all registered users."""
    with database.start_session() as session:
        return session.query(models.User).order_by(models.User.name).all()


def get_user(database: BaseDatabase, uuid: UUID) -> Optional[models.User]:
    """Get specific registered users."""
    with database.start_session() as session:
        return session.query(models.User).get(str(uuid))


def get_direct_children(session: Session, uuid: UUID) -> list[models.Item]:
    """Return all direct children."""
    return session.query(
        models.Item
    ).filter(
        models.Item.parent_uuid == uuid
    ).order_by(
        models.Item.number
    ).all()
