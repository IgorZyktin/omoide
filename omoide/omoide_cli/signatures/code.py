"""Implementation for signatures command."""

from collections.abc import Callable
from collections.abc import Iterator
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
from typing import Literal
import zlib

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from omoide import const
from omoide import custom_logging
from omoide.omoide_cli import common
from omoide.storage.database import db_models

LOG = custom_logging.get_logger(__name__)


def init(
    what: Literal['MD5', 'CRC32'],
    everything: bool,
    folder: str | None,
    db_url: str | None,
) -> tuple[Path, str]:
    """Prepare for running."""
    if everything:
        LOG.info('Recalculating {} hashes for all files', what)
    else:
        LOG.info('Adding {} hashes for files that miss them', what)

    folder = common.extract_env(
        what='File storage path',
        variable=folder,
        env_variable=const.ENV_FOLDER,
    )

    folder_path = Path(folder)

    if not folder_path.exists():
        LOG.error('Storage folder does not exist: {!r}', folder)
        sys.exit(1)

    db_url = common.extract_env(
        what='Database URL',
        variable=db_url,
        env_variable=const.ENV_DB_URL_ADMIN,
    )

    return folder_path, db_url


@dataclass
class Item:
    """Simplified version of an item."""

    id: int
    uuid: str
    owner_uuid: str
    content_ext: str
    prefix_size: int = const.STORAGE_PREFIX_SIZE

    def get_path(self, root: Path) -> Path:
        """Return path to the content file."""
        return (
            root
            / 'content'
            / self.owner_uuid
            / self.uuid[: self.prefix_size]
            / f'{self.uuid}.{self.content_ext}'
        )


def process_items(  # noqa: PLR0913
    what: Literal['MD5', 'CRC32'],
    db_url: str,
    batch_size: int,
    folder_path: Path,
    limit: int | None,
    everything: bool,
    executable: Callable[[Connection, Path, Item], None],
) -> int:
    """Process items in batches."""
    total = 0
    batch_number = 1
    engine = sa.create_engine(db_url, pool_pre_ping=True, future=True)

    def condition(_total_in_batch: int) -> bool:
        """Cycle stop condition."""
        if limit is not None and total == limit:
            return False

        return not (total_in_batch != 0 and total_in_batch < batch_size)

    try:
        with engine.connect() as conn:
            total_in_batch = 0

            while condition(total_in_batch):
                LOG.info('Batch {}', batch_number)
                items = get_items(conn, what, everything, batch_size, limit)

                total_in_batch = 0
                for item in items:
                    executable(conn, folder_path, item)
                    total_in_batch += 1
                    total += 1

                batch_number += 1
    finally:
        engine.dispose()

    return total


def get_items(
    conn: Connection,
    what: Literal['MD5', 'CRC32'],
    everything: bool,
    batch_size: int,
    limit: int | None,
) -> Iterator[Item]:
    """Extract items from the database."""
    common_columns = [
        db_models.Item.id,
        db_models.Item.uuid,
        db_models.Item.owner_uuid,
        db_models.Item.content_ext,
    ]

    if everything:
        query = sa.select(
            *common_columns,
            sa.literal(None),
        )
    elif what == 'MD5':
        query = (
            sa.select(
                *common_columns,
                db_models.SignatureMD5.signature,
            )
            .join(
                db_models.SignatureMD5,
                db_models.Item.id == db_models.SignatureMD5.item_id,
                isouter=True,
            )
            .where(
                db_models.SignatureMD5.signature == sa.null(),
            )
        )
    else:
        query = (
            sa.select(
                *common_columns,
                db_models.SignatureCRC32.signature,
            )
            .join(
                db_models.SignatureCRC32,
                db_models.Item.id == db_models.SignatureCRC32.item_id,
                isouter=True,
            )
            .where(
                db_models.SignatureCRC32.signature == sa.null(),
            )
        )

    # skip items without content
    query = query.where(db_models.Item.content_ext != sa.null()).order_by(
        db_models.Item.id
    )

    if limit is not None:
        query = query.limit(min(batch_size, limit))
    else:
        query = query.limit(batch_size)

    response = conn.execute(query).fetchall()

    for raw_item in response:
        yield Item(
            id=raw_item.id,
            uuid=raw_item.uuid,
            owner_uuid=raw_item.owner_uuid,
            content_ext=raw_item.content_ext,
        )


def update_md5_for_item(conn: Connection, root: Path, item: Item) -> None:
    """Calculate MD5 hash."""
    path = item.get_path(root)
    signature = hashlib.md5(path.read_bytes()).hexdigest()

    LOG.info('Updating {} -> {}', item.uuid, signature)

    insert = pg_insert(db_models.SignatureMD5).values(
        item_id=item.id,
        signature=signature,
    )

    stmt = insert.on_conflict_do_update(
        index_elements=[db_models.SignatureMD5.item_id],
        set_={'signature': insert.excluded.signature},
    )

    conn.execute(stmt)
    conn.commit()


def update_crc32_for_item(conn: Connection, root: Path, item: Item) -> None:
    """Calculate CRC32 hash."""
    path = item.get_path(root)
    signature = zlib.crc32(path.read_bytes())

    LOG.info('Updating {} -> {}', item.uuid, signature)

    insert = pg_insert(db_models.SignatureCRC32).values(
        item_id=item.id,
        signature=signature,
    )

    stmt = insert.on_conflict_do_update(
        index_elements=[db_models.SignatureCRC32.item_id],
        set_={'signature': insert.excluded.signature},
    )

    conn.execute(stmt)
    conn.commit()
