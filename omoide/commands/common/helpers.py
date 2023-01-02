# -*- coding: utf-8 -*-
"""Utils for commands.
"""
import contextlib
import time
from pathlib import Path
from typing import Callable
from typing import Iterator
from typing import Optional
from typing import TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

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


def get_all_corresponding_users(
        session: Session,
        only_user: Optional[UUID],
) -> list[models.User]:
    """Get all users according to config."""
    users: list[models.User] = []
    if only_user:
        user = session.query(models.User).get(str(only_user))

        if user:
            users.append(user)
    else:
        users.extend(
            session.query(
                models.User
            ).order_by(
                models.User.name
            ).all()
        )

    return users


def get_direct_children(session: Session, uuid: UUID) -> list[models.Item]:
    """Return all direct children."""
    return session.query(
        models.Item
    ).filter(
        models.Item.parent_uuid == uuid
    ).order_by(
        models.Item.number
    ).all()


RT = TypeVar('RT', int, None)  # return type


def get_file_size(path: str | Path, default: RT = None) -> Optional[RT]:
    """Get size of the file in bytes."""
    if isinstance(path, str):
        _path = Path(path)
    else:
        _path = path

    try:
        return _path.stat().st_size
    except FileNotFoundError:
        return default
