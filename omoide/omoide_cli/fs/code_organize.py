"""Implementation for organize filesystem command."""

from datetime import datetime
import hashlib
from pathlib import Path
import shutil

import pytz
import sqlalchemy as sa
from sqlalchemy import Connection

from omoide import custom_logging
from omoide import limits
from omoide import models
from omoide.database import db_models

LOG = custom_logging.get_logger(__name__)

ITEMS_CACHE: dict[int, models.Item] = {}
USERS_CACHE: dict[int, models.User] = {}
ALREADY_SEEN: set[str] = set()


def organize(  # noqa: PLR0913
    source: Path,
    archive: Path,
    db_url: str,
    inject_year: bool,
    dry_run: bool,
    timezone: str,
    limit: int,
    delete_empty_folders: bool,
) -> tuple[int, int]:
    """Move files from source folder to archive folder according to item structure."""
    total_files = 0
    total_bytes = 0

    engine = sa.create_engine(db_url, pool_pre_ping=True, future=True)

    with engine.connect() as conn:
        for root, _, files in source.walk():
            for file in files:
                path = root / file

                if path.suffix.lower().lstrip('.') not in limits.SUPPORTED_EXTENSION:
                    continue

                signature = hashlib.md5(path.read_bytes()).hexdigest()

                if signature in ALREADY_SEEN:
                    LOG.warning('Duplicated file: {}', path)
                    continue

                ALREADY_SEEN.add(signature)

                item_id = get_item_id(conn, signature)

                if item_id is None:
                    LOG.warning('Skipping: {}, no item for signature {}', path, signature)
                    continue

                item = get_item(conn, item_id)

                if item is None:
                    continue

                total_files += 1
                total_bytes += path.stat().st_size

                move_single_image(
                    conn=conn,
                    archive=archive,
                    path=path,
                    item=item,
                    inject_year=inject_year,
                    dry_run=dry_run,
                    timezone=timezone,
                    delete_empty_folders=delete_empty_folders,
                )

                if total_files >= limit > -1:
                    return total_files, total_bytes

    return total_files, total_bytes


def get_item_id(conn: Connection, signature: str) -> int | None:
    """Get item_id for given signature."""
    query = sa.select(db_models.SignatureMD5.item_id).where(
        db_models.SignatureMD5.signature == signature
    )
    response = conn.execute(query).fetchall()

    for (item_id,) in response:
        # some signatures are belong to collections, not item themselves
        item = get_item(conn, item_id)
        if item is not None and not item.is_collection:
            return item.id

    return None


def get_item(conn: Connection, item_id: int) -> models.Item | None:
    """Get item object."""
    item = ITEMS_CACHE.get(item_id)

    if item is not None:
        return item

    query = sa.select(db_models.Item).where(
        db_models.Item.id == item_id,
        db_models.Item.status != models.Status.DELETED,
    )
    response = conn.execute(query).fetchone()

    if response is None:
        return None

    item = models.Item.from_obj(response)
    ITEMS_CACHE[item.id] = item
    return item


def get_user(conn: Connection, user_id: int) -> models.User:
    """Get user object."""
    user = USERS_CACHE.get(user_id)

    if user is not None:
        return user

    query = sa.select(db_models.User).where(db_models.User.id == user_id)
    response = conn.execute(query).fetchone()
    assert response is not None

    user = models.User.from_obj(response)
    USERS_CACHE[user.id] = user
    return user


def get_parents(conn: Connection, item: models.Item) -> list[models.Item]:
    """Return list of parents for given item."""
    parents: list[models.Item] = []
    parent_id = item.parent_id

    while parent_id is not None:
        parent = get_item(conn, parent_id)

        if parent is None:
            break

        parents.append(parent)
        parent_id = parent.parent_id

    return list(reversed(parents))


def move_single_image(  # noqa: PLR0913
    conn: Connection,
    archive: Path,
    path: Path,
    item: models.Item,
    inject_year: bool,
    dry_run: bool,
    timezone: str,
    delete_empty_folders: bool,
) -> None:
    """Put image into archive."""
    owner = get_user(conn, item.owner_id)

    resulting_path = archive / owner.name

    if inject_year:
        timestamp = min(path.stat().st_ctime, path.stat().st_mtime)
        year = datetime.fromtimestamp(timestamp, tz=pytz.timezone(timezone)).date().year
        resulting_path = resulting_path / str(year)

    parents = get_parents(conn, item)

    for parent in parents:
        if parent.name == owner.name:
            continue
        resulting_path = resulting_path / parent.name

    if dry_run:
        LOG.warning('Will move {} -> {}', path, resulting_path / path.name)
    else:
        LOG.info('Moving {} -> {}', path, resulting_path / path.name)
        resulting_path.mkdir(parents=True, exist_ok=True)
        shutil.move(
            src=path,
            dst=resulting_path / path.name,
        )

        if delete_empty_folders:
            do_delete_empty_folders(archive, path)


def do_delete_empty_folders(archive: Path, path: Path) -> None:
    """Remove directories without files."""
    if path == archive:
        return

    parent = path.parent

    while not list(parent.iterdir()):
        LOG.warning('Removing empty {}', path.parent)
        answer = input('Press y to delete')
        if answer.strip() == 'y':
            shutil.rmtree(path.parent)
            parent = parent.parent
        else:
            break
