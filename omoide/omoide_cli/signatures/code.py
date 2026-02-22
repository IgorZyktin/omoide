"""Check signatures."""

from collections.abc import Iterator
import hashlib
from pathlib import Path
from typing import Any
from uuid import UUID
import zlib

import sqlalchemy as sa
from sqlalchemy import Connection
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import models
from omoide import utils
from omoide.database import db_models


def fix_missing_signatures(
    engine: Engine,
    data_folder: Path,
    site_url: str,
    fix_missing: bool,
    marker: int,
    limit: int,
) -> None:
    """Create signatures for items that miss them."""
    with engine.begin() as conn:
        for id_, user_uuid, item_uuid, ext in _get_items_without_signatures(conn, marker, limit):
            string = f'Missing: item_id={id_}, {site_url}/preview/{item_uuid}'
            if fix_missing:
                _update_signature(conn, data_folder, id_, user_uuid, item_uuid, ext)
                string += ' [Fixed]'

            print(string)  # noqa: T201


def _get_items_without_signatures(conn: Connection, marker: int, limit: int) -> Iterator[tuple]:
    """Get info from DB."""
    query = (
        sa.select(
            db_models.Item.id,
            db_models.User.uuid,
            db_models.Item.uuid,
            db_models.Item.content_ext,
        )
        .join(
            db_models.User,
            db_models.User.id == db_models.Item.owner_id,
            isouter=True,
        )
        .join(
            db_models.SignatureMD5,
            db_models.SignatureMD5.item_id == db_models.Item.id,
            isouter=True,
        )
        .join(
            db_models.SignatureCRC32,
            db_models.SignatureCRC32.item_id == db_models.Item.id,
            isouter=True,
        )
        .where(
            db_models.Item.status == models.Status.AVAILABLE,
            db_models.Item.content_ext != sa.null(),
            sa.or_(
                db_models.SignatureMD5.signature == sa.null(),
                db_models.SignatureCRC32.signature == sa.null(),
            ),
            db_models.Item.id > marker,
        )
        .order_by(db_models.Item.id)
        .limit(limit)
    )

    response = conn.execute(query).all()
    yield from response


def _update_signature(
    conn: Connection,
    data_folder: Path,
    item_id: int,
    user_uuid: UUID,
    item_uuid: UUID,
    ext: str,
    md5: str | None = None,
    crc32: str | None = None,
) -> None:
    """Update signature for a file."""
    path = utils.get_content_path(data_folder, user_uuid, item_uuid, ext)

    md5 = md5 or hashlib.md5(path.read_bytes()).hexdigest()
    insert_md5 = pg_insert(db_models.SignatureMD5).values(
        item_id=item_id,
        signature=md5,
    )
    stmt_md5 = insert_md5.on_conflict_do_update(
        index_elements=[db_models.SignatureMD5.item_id],
        set_={'signature': insert_md5.excluded.signature},
    )

    crc32 = crc32 or zlib.crc32(path.read_bytes())
    insert_crc32 = pg_insert(db_models.SignatureCRC32).values(
        item_id=item_id,
        signature=crc32,
    )
    stmt_crc32 = insert_crc32.on_conflict_do_update(
        index_elements=[db_models.SignatureCRC32.item_id],
        set_={'signature': insert_crc32.excluded.signature},
    )

    conn.execute(stmt_md5)
    conn.execute(stmt_crc32)


def fix_mismatching_signatures(
    engine: Engine,
    data_folder: Path,
    site_url: str,
    fix_mismatching: bool,
    marker: int,
    limit: int,
) -> list[dict[str, Any]]:
    """Create signatures for items that miss them."""
    diff: list[dict[str, Any]] = []

    id_ = None
    with engine.begin() as conn:
        for id_, user_uuid, item_uuid, ext, md5, crc32, dt, size in _get_all_signatures(conn,
                                                                                        marker,
                                                                                        limit):
            path = utils.get_content_path(data_folder, user_uuid, item_uuid, ext)
            real_md5 = hashlib.md5(path.read_bytes()).hexdigest()
            real_crc32 = zlib.crc32(path.read_bytes())

            print(f'\rProcessing: {id_}', end='')  # noqa: T201

            if real_md5 != md5 or real_crc32 != crc32:
                string = f'\rMismatching: item_id={id_}, {site_url}/preview/{item_uuid}'

                diff.append(
                    {
                        'id': id_,
                        'user_uuid': str(user_uuid),
                        'item_uuid': str(item_uuid),
                        'ext': ext,
                        'database_md5': md5,
                        'database_crc32': crc32,
                        'real_md5': real_md5,
                        'real_crc32': real_crc32,
                        'timestamp': dt.isoformat(),
                        'size': size,
                        'url': f'{site_url}/preview/{item_uuid}',
                    }
                )

                if fix_mismatching:
                    _update_signature(
                        conn,
                        data_folder,
                        id_,
                        user_uuid,
                        item_uuid,
                        ext,
                        md5=md5,
                        crc32=crc32,
                    )
                    string += ' [Fixed]'

                print(string)  # noqa: T201

    if id_ is not None:
        print(f'Last item id: {id_}')  # noqa: T201

    return diff


def _get_all_signatures(conn: Connection, marker: int, limit: int) -> Iterator[tuple]:
    """Get info from DB."""
    query = (
        sa.select(
            db_models.Item.id,
            db_models.User.uuid,
            db_models.Item.uuid,
            db_models.Item.content_ext,
            sa.label('md5', db_models.SignatureMD5.signature),
            sa.label('crc32', db_models.SignatureCRC32.signature),
            db_models.Metainfo.created_at,
            db_models.Metainfo.content_size,
        )
        .join(
            db_models.User,
            db_models.User.id == db_models.Item.owner_id,
            isouter=True,
        )
        .join(
            db_models.SignatureMD5,
            db_models.SignatureMD5.item_id == db_models.Item.id,
            isouter=True,
        )
        .join(
            db_models.SignatureCRC32,
            db_models.SignatureCRC32.item_id == db_models.Item.id,
            isouter=True,
        )
        .join(
            db_models.Metainfo,
            db_models.Metainfo.item_id == db_models.Item.id,
            isouter=True,
        )
        .where(
            db_models.Item.status == models.Status.AVAILABLE,
            db_models.Item.content_ext != sa.null(),
            db_models.SignatureMD5.signature != sa.null(),
            db_models.SignatureCRC32.signature != sa.null(),
            db_models.Item.id > marker,
        )
        .order_by(db_models.Item.id)
        .limit(limit)
    )

    response = conn.execute(query).all()
    yield from response
