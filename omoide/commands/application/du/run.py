# -*- coding: utf-8 -*-
"""Disk Usage command.
"""
import dataclasses
import functools

import sqlalchemy as sa
from prettytable import PrettyTable
from sqlalchemy.orm import Session

from omoide import utils
from omoide.commands.application.du.cfg import Config
from omoide.commands.common import helpers
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging
from omoide.storage.database import models

LOG = custom_logging.get_logger(__name__)


def run(
        database: BaseDatabase,
        config: Config,
) -> None:
    """Show disk usage for users."""
    verbose_config = [
        f'\t{key}={value},\n'
        for key, value in config.dict().items()
    ]
    LOG.info(f'Config:\n{{\n{"".join(verbose_config)}}}')

    with Session(database.engine) as session:
        users = helpers.get_all_corresponding_users(
            session=session,
            only_users=config.only_users,
        )

    stats: list[Stats] = []
    for user in users:
        new_stats = scan_for_user(session, user)
        stats.append(new_stats)

    describe_result(stats)


@dataclasses.dataclass
class Stats:
    """Helper class that stores stats for a user."""
    user: models.User
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


def scan_for_user(
        session: Session,
        user: models.User,
) -> Stats:
    """Calculate sizes for specific user."""
    stmt = sa.select(
        sa.func.coalesce(
            sa.func.sum(models.Metainfo.content_size), 0
        ).label('content_size'),
        sa.func.coalesce(
            sa.func.sum(models.Metainfo.preview_size), 0
        ).label('preview_size'),
        sa.func.coalesce(
            sa.func.sum(models.Metainfo.thumbnail_size), 0
        ).label('thumbnail_size'),
        sa.func.count(models.Item.content_ext).label('content_total'),
        sa.func.count(models.Item.preview_ext).label('preview_total'),
        sa.func.count(models.Item.thumbnail_ext).label('thumbnail_total'),
        sa.func.count(models.Item.uuid).label('total_items'),
    ).join(
        models.Item,
        models.Metainfo.item_uuid == models.Item.uuid,
    ).where(
        models.Item.owner_uuid == user.uuid
    )

    response = session.execute(stmt).fetchone()

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
