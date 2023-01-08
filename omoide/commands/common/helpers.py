# -*- coding: utf-8 -*-
"""Utils for commands.
"""
import contextlib
import time
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Iterator
from typing import Optional
from typing import TypeVar
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

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
        only_users: list[UUID],
) -> list[models.User]:
    """Get all users according to config."""
    query = session.query(models.User)

    if only_users:
        query = query.filter(
            models.User.uuid.in_(tuple(str(x) for x in only_users))  # noqa
        )

    return query.order_by(models.User.name).all()


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


def get_file_size(path: str | Path, default: RT = None) -> RT:
    """Get size of the file in bytes."""
    if isinstance(path, str):
        _path = Path(path)
    else:
        _path = path

    try:
        return _path.stat().st_size
    except FileNotFoundError:
        return default


def get_children(
        session: Session,
        item: models.Item,
) -> list[models.Item]:
    """Get child items."""
    query = session.query(
        models.Item
    ).where(
        models.Item.parent_uuid == item.uuid,
    ).order_by(
        models.Item.number
    )

    return query.all()


def output_tree(
        session: Session,
        item: models.Item,
        depth: int = 0,
) -> None:
    """Debug tool that show whole tree stating from some item."""
    tab = '\t' * depth + '┗━ '
    children = get_children(session, item)
    print(f'{tab}{item.uuid} {item.name or "???"} -> {len(children)} children')

    for child in children:
        output_tree(session, child, depth + 1)


def get_metainfo(
        session: Session,
        item: models.Item,
) -> models.Metainfo:
    """Get metainfo for given item."""
    metainfo = session.query(
        models.Metainfo
    ).where(
        models.Metainfo.item_uuid == str(item.uuid)
    ).first()

    if metainfo is None:
        raise RuntimeError(f'No metainfo for item {item.uuid}')

    return metainfo


def get_item(
        session: Session,
        item_uuid: UUID,
) -> models.Item:
    """Get item but only if it is collection."""
    item = session.query(
        models.Item
    ).where(
        models.Item.uuid == str(item_uuid),
    ).first()

    if item is None:
        raise RuntimeError(f'Item {item_uuid} does not exist')

    return item


def insert_into_metainfo_extras(
        session: Session,
        metainfo: models.Metainfo,
        new_data: dict[str, Any],
) -> None:
    """Insert new keys and values to JSONB field in metainfo."""
    for key, value in new_data.items():
        stmt = sa.update(
            models.Metainfo
        ).where(
            models.Metainfo.item_uuid == metainfo.item_uuid
        ).values(
            extras=sa.func.jsonb_set(
                models.Metainfo.extras,
                [key],
                f'"{value}"' if isinstance(value, str) else value,
            )
        )
        flag_modified(metainfo, 'extras')
        session.execute(stmt)
