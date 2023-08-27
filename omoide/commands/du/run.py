"""Disk Usage command.
"""
import dataclasses
import functools

import sqlalchemy as sa
from prettytable import PrettyTable
from sqlalchemy.engine import Connection

from omoide import utils
from omoide.commands import helpers
from omoide.commands.du.cfg import Config
from omoide.infra import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(config: Config, database: SyncDatabase) -> None:
    """Show disk usage for users."""
    LOG.info('\nConfig:\n{}', utils.serialize_model(config))

    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(session, config.only_users)

    with database.start_transaction() as conn:
        stats: list[Stats] = []
        for user in users:
            new_stats = scan_for_user(conn, user)
            stats.append(new_stats)

    describe_result(stats)


@dataclasses.dataclass
class Stats:
    """Helper class that stores stats for a user."""
    user: db_models.User
    content_size: int
    preview_size: int
    thumbnail_size: int
    content_total: int
    preview_total: int
    thumbnail_total: int
    total_items: int

    @functools.cached_property
    def total_files(self) -> int:
        """Return summary of files count."""
        return sum((
            self.content_total,
            self.preview_total,
            self.thumbnail_total,
        ))

    @functools.cached_property
    def total_size(self) -> int:
        """Return summary of size count."""
        return sum((
            self.content_size,
            self.preview_size,
            self.thumbnail_size,
        ))

    def calc_percent_of_files(self, total_files: int) -> float:
        """Return part that user takes in all files."""
        if self.total_files == 0:
            return 0.0
        return (self.total_files / total_files) * 100

    def calc_percent_of_size(self, total_size: int) -> float:
        """Return part that user takes in all stored bytes."""
        if self.total_size == 0:
            return 0.0
        return (self.total_size / total_size) * 100


def scan_for_user(conn: Connection, user: db_models.User) -> Stats:
    """Calculate sizes for specific user."""
    stmt = sa.select(
        sa.func.coalesce(
            sa.func.sum(db_models.Metainfo.content_size), 0
        ).label('content_size'),
        sa.func.coalesce(
            sa.func.sum(db_models.Metainfo.preview_size), 0
        ).label('preview_size'),
        sa.func.coalesce(
            sa.func.sum(db_models.Metainfo.thumbnail_size), 0
        ).label('thumbnail_size'),
        sa.func.count(db_models.Item.content_ext).label('content_total'),
        sa.func.count(db_models.Item.preview_ext).label('preview_total'),
        sa.func.count(db_models.Item.thumbnail_ext).label('thumbnail_total'),
        sa.func.count(db_models.Item.uuid).label('total_items'),
    ).join(
        db_models.Item,
        db_models.Metainfo.item_uuid == db_models.Item.uuid,
    ).where(
        db_models.Item.owner_uuid == user.uuid
    )

    response = conn.execute(stmt).fetchone()

    if response is None:
        return Stats(
            user=user,
            content_size=-1,
            preview_size=-1,
            thumbnail_size=-1,
            content_total=-1,
            preview_total=-1,
            thumbnail_total=-1,
            total_items=-1,
        )

    return Stats(
        user=user,
        content_size=response['content_size'],
        preview_size=response['preview_size'],
        thumbnail_size=response['thumbnail_size'],
        content_total=response['content_total'],
        preview_total=response['preview_total'],
        thumbnail_total=response['thumbnail_total'],
        total_items=response['total_items'],
    )


def describe_result(
        stats: list[Stats],
) -> None:
    """Print result."""
    table = PrettyTable()

    table.field_names = [
        'Number',
        'User UUID',
        'User name',
        'Total items',
        'Content files',
        'Preview files',
        'Thumbnail files',
        'Total files',
        'Content size',
        'Preview size',
        'Thumbnail size',
        'Total used size',
        'Percent of files',
        'Percent of size',
    ]

    total_files = 0
    total_size = 0
    total_items = 0

    for each_stat in stats:
        total_files += each_stat.total_files
        total_size += each_stat.total_size
        total_items += each_stat.total_items

    stats.sort(
        key=lambda self: self.calc_percent_of_size(total_size),
        reverse=True,
    )

    digits = len(str(len(stats)))
    template = f'{{:0{digits}d}}'

    i = 0
    for stat in stats:
        if stat.calc_percent_of_size(total_size) < 0.1:
            continue

        i += 1
        number = template.format(i)
        table.add_row([
            number,
            stat.user.uuid,
            stat.user.name,
            utils.sep_digits(stat.total_items),
            utils.sep_digits(stat.content_total),
            utils.sep_digits(stat.preview_total),
            utils.sep_digits(stat.thumbnail_total),
            utils.sep_digits(stat.total_files),
            utils.byte_count_to_text(stat.content_size),
            utils.byte_count_to_text(stat.preview_size),
            utils.byte_count_to_text(stat.thumbnail_size),
            utils.byte_count_to_text(stat.total_size),
            f'{round(stat.calc_percent_of_files(total_files), 2)} %',
            f'{round(stat.calc_percent_of_size(total_size), 2)} %',
        ])

    print(table.get_string())
    print(f'Total items: {utils.sep_digits(total_items)}')
    print(f'Total files: {utils.sep_digits(total_files)}')
    print(f'Total size: {utils.byte_count_to_text(total_size)}')
