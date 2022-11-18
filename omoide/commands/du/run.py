# -*- coding: utf-8 -*-
"""Disk Usage command.
"""
import concurrent
import concurrent.futures
import os
from collections import defaultdict
from pathlib import Path
from typing import Iterator
from uuid import UUID

from sqlalchemy.engine import Engine

from omoide import utils
from omoide.commands.du import database
from omoide.commands.du.cfg import Config
from omoide.commands.du.stats import Stats


def main(
        engine: Engine,
        config: Config,
) -> None:
    """Show disk usage for every user."""
    stats = scan(engine, config)
    describe_result(stats)


def scan(
        engine: Engine,
        config: Config,
) -> Stats:
    """Gather information."""
    folders = [
        Path(config.cold_folder) / 'content',
        Path(config.cold_folder) / 'preview',
        Path(config.cold_folder) / 'thumbnail',
    ]

    stats = Stats()

    for folder in folders:
        if not folder.exists():
            print(f'Folder {folder.name} does not exist!')
            continue

        files_counter = scan_top_level_folder(engine, folder, stats)

        for user, maximum in files_counter.items():
            if isinstance(user, bytes):
                stats.store_files_counter(user.decode(), maximum)
            else:
                stats.store_files_counter(user, maximum)

    return stats


W_NUMBER = 3
W_UUID = 36
W_NAME = 16
W_FILES = 16
W_BYTES = 16


def _str(value: str, width: int) -> str:
    """Safe convert to string."""
    value = value[:width]
    return value.center(width)


def _prc(part: int | float, total: int | float) -> str:
    """Safe convert to percent."""
    if not part:
        return '0.00 %'

    percent = part / total * 100
    return f'{percent:0.2f} %'


def describe_result(
        stats: Stats
) -> None:
    """Print result."""
    users = sorted(
        stats.users.values(),
        key=lambda user: user.total_size,
        reverse=True,
    )

    total_size = sum(user.total_size for user in users)

    def _print_line():
        print('+' + ' + '.join([
            _str('-' * W_NUMBER, W_NUMBER),
            _str('-' * W_UUID, W_UUID),
            _str('-' * W_NAME, W_NAME),
            _str('-' * W_FILES, W_FILES),
            _str('-' * W_FILES, W_FILES),
            _str('-' * W_FILES, W_FILES),
            _str('-' * W_BYTES, W_BYTES),
            _str('-' * W_BYTES, W_BYTES),
            _str('-' * W_BYTES, W_BYTES),
            _str('-' * W_BYTES, W_BYTES),
            _str('-' * W_BYTES, W_BYTES),
        ]) + '+')

    _print_line()

    print('|' + ' | '.join([
        _str('N', W_NUMBER),
        _str('UUID', W_UUID),
        _str('User name', W_NAME),
        _str('Content files', W_FILES),
        _str('Preview files', W_FILES),
        _str('Thumbnail files', W_FILES),
        _str('Content size', W_BYTES),
        _str('Preview size', W_BYTES),
        _str('Thumbnail size', W_BYTES),
        _str('Total size', W_BYTES),
        _str('Percent', W_BYTES),
    ]) + '|')

    _print_line()
    for i, user in enumerate(users, start=1):
        uuid = f'{str(user.uuid):36}'
        name = user.name
        content_files = utils.sep_digits(user.files['content'], 0)
        preview_files = utils.sep_digits(user.files['preview'], 0)
        thumbnail_files = utils.sep_digits(user.files['thumbnail'], 0)
        content_size = utils.byte_count_to_text(user.bytes['content'])
        preview_size = utils.byte_count_to_text(user.bytes['preview'])
        thumbnail_size = utils.byte_count_to_text(user.bytes['thumbnail'])
        total_user_size = (user.bytes['content']  # noqa: W503
                           + user.bytes['preview']  # noqa: W503
                           + user.bytes['thumbnail'])  # noqa: W503

        print('|' + ' | '.join([
            _str(str(i), W_NUMBER),
            _str(uuid, W_UUID),
            _str(name, W_NAME),
            _str(content_files, W_FILES),
            _str(preview_files, W_FILES),
            _str(thumbnail_files, W_FILES),
            _str(content_size, W_BYTES),
            _str(preview_size, W_BYTES),
            _str(thumbnail_size, W_BYTES),
            _str(utils.byte_count_to_text(total_user_size), W_BYTES),
            _str(_prc(user.total_size, total_size), W_BYTES),
        ]) + '|')

    _print_line()

    total_content_files = sum(user.files['content']
                              for user in stats.users.values())
    total_preview_files = sum(user.files['preview']
                              for user in stats.users.values())
    total_thumbnail_files = sum(user.files['thumbnail']
                                for user in stats.users.values())

    total_content_size = sum(user.bytes['content']
                             for user in
                             stats.users.values())
    total_preview_size = sum(user.bytes['preview']
                             for user in
                             stats.users.values())
    total_thumbnail_size = sum(user.bytes['thumbnail']
                               for user in
                               stats.users.values())

    print('|' + ' | '.join([
        _str(' ', W_NUMBER),
        _str(' ', W_UUID),
        _str('TOTAL', W_NAME),

        _str(str(utils.sep_digits(total_content_files)), W_FILES),
        _str(str(utils.sep_digits(total_preview_files)), W_FILES),
        _str(str(utils.sep_digits(total_thumbnail_files)), W_FILES),

        _str(str(utils.byte_count_to_text(total_content_size)),
             W_BYTES),
        _str(str(utils.byte_count_to_text(total_preview_size)),
             W_BYTES),
        _str(str(utils.byte_count_to_text(total_thumbnail_size)),
             W_BYTES),
        _str('100.00 %', W_BYTES),
        _str(' ', W_BYTES),
    ]) + '|')

    _print_line()

    total_files = (total_content_files  # noqa: W503
                   + total_preview_files  # noqa: W503
                   + total_thumbnail_files) or 1  # noqa: W503

    total_size = total_size or 1

    print('|' + ' | '.join([
        _str(' ', W_NUMBER),
        _str(' ', W_UUID),
        _str(' ', W_NAME),

        _str(_prc(total_content_files, total_files), W_FILES),
        _str(_prc(total_preview_files, total_files), W_FILES),
        _str(_prc(total_thumbnail_files, total_files), W_FILES),

        _str(_prc(total_content_size, total_size), W_BYTES),
        _str(_prc(total_preview_size, total_size), W_BYTES),
        _str(_prc(total_thumbnail_size, total_size), W_BYTES),

        _str(' ', W_BYTES),
        _str(' ', W_BYTES),
    ]) + '|')

    _print_line()

    max_files = sorted(stats.max_files.items(),
                       key=lambda x: x[1], reverse=True)
    if max_files:
        print(f'Maximum files: {max_files[0][0]}: {max_files[0][1]}')


def scan_top_level_folder(
        engine: Engine,
        path: Path,
        stats: Stats,
) -> dict[bytes, int]:
    """Gather info about top level folder."""
    users = os.listdir(path)
    futures = []
    files_counter: dict[bytes, int] = defaultdict(int)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for user in users:
            uuid = UUID(str(user))
            files = scan_user_folder(engine, path, stats, uuid)

            total_files = 0
            for file in files:
                futures.append(executor.submit(get_size, uuid, file))
                total_files += 1

            files_counter[user] = len(os.listdir(path / str(uuid)))

        for future in concurrent.futures.as_completed(futures):
            uuid, size = future.result()
            stats.store_size(uuid, path, file, size)

    return files_counter


def scan_user_folder(
        engine: Engine,
        path: Path,
        stats: Stats,
        uuid: UUID,
) -> Iterator:
    """Scan personal user folder."""
    user = database.get_user(engine, uuid)
    stats.store_user(uuid, user.name if user else 'Unknown user')

    for sub_folder in os.scandir(path / str(uuid)):
        for file in os.scandir(path / str(uuid) / sub_folder):
            yield file


def get_size(uuid: UUID, path: Path) -> tuple[UUID, int]:
    """Get size of the file."""
    return uuid, path.stat().st_size
