"""Code for the `du` command."""

from collections import defaultdict
from dataclasses import dataclass
import functools
from typing import Any
from typing import Literal
from uuid import UUID

import colorama
from prettytable import PrettyTable
import sqlalchemy as sa
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from omoide import utils
from omoide.database import db_models


def get_all_corresponding_users(
    session: Session,
    only_users: list[UUID] | None,
) -> list[db_models.User]:
    """Get all users according to arguments."""
    if only_users is None:
        return session.query(db_models.User).all()

    return (
        session.query(db_models.User)
        .filter(db_models.User.uuid.in_(only_users))
        .all()
    )


@dataclass
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
        return sum(
            (
                self.content_total,
                self.preview_total,
                self.thumbnail_total,
            )
        )

    @functools.cached_property
    def total_size(self) -> int:
        """Return summary of size count."""
        return sum(
            (
                self.content_size,
                self.preview_size,
                self.thumbnail_size,
            )
        )

    def percent(self, what: str, of: str, total: int) -> str:
        """Return percent of given attribute value."""
        value = getattr(self, f'{what}_{of}')

        if value == 0:
            return '0.00'

        percent = (value / total) * 100.0
        return f'{percent:.2f}'


def scan_for_user(conn: Connection, user: db_models.User) -> Stats:
    """Calculate disk usage for specific user."""
    stmt = (
        sa.select(
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
            sa.func.count(db_models.Item.thumbnail_ext).label(
                'thumbnail_total'
            ),
            sa.func.count(db_models.Item.uuid).label('total_items'),
        )
        .join(
            db_models.Item,
            db_models.Metainfo.item_uuid == db_models.Item.uuid,
        )
        .where(db_models.Item.owner_uuid == user.uuid)
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
        content_size=response.content_size,
        preview_size=response.preview_size,
        thumbnail_size=response.thumbnail_size,
        content_total=response.content_total,
        preview_total=response.preview_total,
        thumbnail_total=response.thumbnail_total,
        total_items=response.total_items,
    )


def _highlight(text: Any) -> str:
    """Make this row more visible."""
    return f'{colorama.Fore.LIGHTGREEN_EX}{text}{colorama.Fore.RESET}'


def print_results(stats: list[Stats], threshold: float = 0.1) -> None:
    """Print table with all results."""
    table = PrettyTable()

    table.field_names = [
        'Number',
        'User UUID',
        'User name',
        'Content',
        'Preview',
        'Thumbnail',
        'Total',
    ]

    total: dict[str, int] = defaultdict(int)

    for each_stat in stats:
        total['files'] += each_stat.total_files
        total['size'] += each_stat.total_size
        total['items'] += each_stat.total_items
        total['content_total'] += each_stat.content_total
        total['preview_total'] += each_stat.preview_total
        total['thumbnail_total'] += each_stat.thumbnail_total
        total['content_size'] += each_stat.content_size
        total['preview_size'] += each_stat.preview_size
        total['thumbnail_size'] += each_stat.thumbnail_size

    stats.sort(
        key=lambda self: float(self.percent('total', 'size', total['size'])),
        reverse=True,
    )

    stats = [
        each_stat
        for each_stat in stats
        if float(each_stat.percent('total', 'size', total['size'])) > threshold
    ]

    digits = len(str(len(stats)))
    template = f'{{:0{digits}d}}'

    def _format(
        _stat: Stats,
        what: Literal['content', 'preview', 'thumbnail'],
        the_last_one: bool,
    ) -> str:
        """Format multiline summary."""
        lines = [
            _highlight(utils.sep_digits(getattr(_stat, f'{what}_total'))),
            _stat.percent(what, 'total', total[f'{what}_total'])
            + '% of files',
            _stat.percent(what, 'size', total[f'{what}_size']) + '% of size',
        ]

        if not the_last_one:
            lines.append('\n')

        return '\n'.join(lines)

    for position, stat in enumerate(stats, start=1):
        number = template.format(position)
        table.add_row(
            [
                _highlight(number),
                _highlight(stat.user.uuid),
                _highlight(stat.user.name),
                _format(stat, 'content', position == len(stats)),
                _format(stat, 'preview', position == len(stats)),
                _format(stat, 'thumbnail', position == len(stats)),
                (
                    _highlight(utils.sep_digits(stat.total_files) + ' files')
                    + '\n'
                    + utils.human_readable_size(stat.total_size)
                ),
            ]
        )

    print(table.get_string())  # noqa: T201
    print('Total:')  # noqa: T201
    print('\t' + utils.sep_digits(total['items']) + ' items')  # noqa: T201
    print('\t' + utils.sep_digits(total['files']) + ' files')  # noqa: T201
    print('\t' + utils.human_readable_size(total['size']))  # noqa: T201
