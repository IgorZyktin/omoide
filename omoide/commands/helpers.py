"""Utils for commands."""

from collections.abc import Callable
from collections.abc import Iterator
import contextlib
from pathlib import Path
import time
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from omoide import utils
from omoide.database import db_models

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

    def _maybe_print(template: str | None, **kwargs: Any) -> None:
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
    only_users: list[str],
) -> list[db_models.User]:
    """Get all users according to config."""
    query = session.query(db_models.User)

    uuids = []
    strings = []
    for user_string in only_users:
        if utils.is_valid_uuid(user_string):
            uuids.append(user_string)
        else:
            strings.append(user_string)

    if only_users:
        query = query.filter(
            sa.or_(
                db_models.User.uuid.in_(uuids),  # noqa
                db_models.User.login.in_(strings),  # noqa
                db_models.User.name.in_(strings),  # noqa
            )
        )

    return query.order_by(db_models.User.name).all()


def get_file_size(
    path: str | Path,
    default: int | None = None,
) -> int | None:
    """Get size of the file in bytes."""
    if isinstance(path, str):
        _path = Path(path)
    else:
        _path = path

    try:
        return _path.stat().st_size
    except FileNotFoundError:
        return default


def get_metainfo(
    session: Session,
    item: db_models.Item,
) -> db_models.Metainfo:
    """Get metainfo for given item."""
    metainfo = (
        session.query(db_models.Metainfo).where(db_models.Metainfo.item_id == item.id).first()
    )

    if metainfo is None:
        msg = f'No metainfo for item {item.uuid}'
        raise RuntimeError(msg)

    return metainfo


def get_item(
    session: Session,
    item_uuid: UUID,
) -> db_models.Item:
    """Get item but only if it is collection."""
    item = (
        session.query(db_models.Item)
        .where(
            db_models.Item.uuid == str(item_uuid),
        )
        .first()
    )

    if item is None:
        msg = f'Item {item_uuid} does not exist'
        raise RuntimeError(msg)

    return item


def insert_item_note(
    session: Session,
    item: db_models.Item,
    key: str,
    value: str,
) -> None:
    """Insert new keys in notes."""
    insert = pg_insert(db_models.ItemNote).values(
        item_id=item.id,
        key=key,
        value=value,
    )

    stmt = insert.on_conflict_do_update(
        index_elements=[
            db_models.ItemNote.item_id,
            db_models.ItemNote.key,
        ],
        set_={'value': insert.excluded.value},
    )

    session.execute(stmt)
