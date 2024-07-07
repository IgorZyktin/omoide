"""Utils for commands."""
import contextlib
import time
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Iterator
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from omoide import domain
from omoide import utils
from omoide.storage.database import db_models

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
        default: Optional[int] = None,
) -> Optional[int]:
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
        item: domain.Item,
) -> list[db_models.Item]:
    """Get child items."""
    query = session.query(
        db_models.Item
    ).where(
        db_models.Item.parent_uuid == item.uuid,
    ).order_by(
        db_models.Item.number
    )

    return query.all()


def output_tree(
        session: Session,
        item: domain.Item,
        show_uuids: bool = False,
        position: str = 'last',
        depth: int = 0,
        callback: Callable = print,
) -> None:
    """Debug tool that show whole tree stating from some item."""
    if position == 'middle':
        prefix = '┣━ '
    else:
        prefix = '┗━ '

    if depth:
        tab = '\t' * depth + prefix
    else:
        tab = ''

    children = get_children(session, item)

    if children or item.is_collection:
        if show_uuids:
            label = f'{item.uuid} {item.name or "???"}'
        else:
            label = f'{item.name or "???"}'

        callback(f'{tab}{label} -> {len(children)} children')

    for i, child in enumerate(children, start=1):
        if i < len(children):
            position = 'middle'
        else:
            position = 'last'

        output_tree(
            session,
            child,
            show_uuids=show_uuids,
            position=position,
            depth=depth + 1,
            callback=callback,
        )


def get_metainfo(
        session: Session,
        item: db_models.Item,
) -> db_models.Metainfo:
    """Get metainfo for given item."""
    metainfo = session.query(
        db_models.Metainfo
    ).where(
        db_models.Metainfo.item_uuid == str(item.uuid)
    ).first()

    if metainfo is None:
        raise RuntimeError(f'No metainfo for item {item.uuid}')

    return metainfo


def get_item(
        session: Session,
        item_uuid: UUID,
) -> db_models.Item:
    """Get item but only if it is collection."""
    item = session.query(
        db_models.Item
    ).where(
        db_models.Item.uuid == str(item_uuid),
    ).first()

    if item is None:
        raise RuntimeError(f'Item {item_uuid} does not exist')

    return item


def insert_into_metainfo_extras(
        session: Session,
        metainfo: db_models.Metainfo,
        new_data: dict[str, Any],
) -> None:
    """Insert new keys and values to JSONB field in metainfo."""
    for key, value in new_data.items():
        stmt = sa.update(
            db_models.Metainfo
        ).where(
            db_models.Metainfo.item_uuid == metainfo.item_uuid
        ).values(
            extras=sa.func.jsonb_set(
                db_models.Metainfo.extras,
                [key],
                f'"{value}"' if isinstance(value, str) else value,
            )
        )
        flag_modified(metainfo, 'extras')
        session.execute(stmt)
