# -*- coding: utf-8 -*-
"""Downloader daemon.

Downloads processed images from database to the local storages(s).
We're using database as a medium.
"""
from types import FunctionType

import click

from omoide.daemons.common import action_class
from omoide.daemons.common import out
from omoide.daemons.downloader import cfg
from omoide.daemons.downloader import db

DECORATORS = (
    click.command(),
    click.option('--silent/--no-silent',
                 default=False,
                 help='Print output during work or just do it silently'),
    click.option('--dry-run/--no-dry-run',
                 default=True,
                 help='Run script, but do not save changes'),
    click.option('--strict/--no-strict',
                 default=True,
                 help='Stop processing on first error or try to complete all'),
    click.option('--batch-size',
                 default=50,
                 help='Process not more than this amount of objects at once'),
    click.option('--limit',
                 default=-1,
                 help='Maximum amount of items to process (-1 for infinity)'),
)


def cli_arguments(func: FunctionType) -> FunctionType:
    """Apply CLI arguments to a given entry point."""
    decorators = reversed(DECORATORS)

    for decorator in decorators:
        func = decorator(func)

    return func


def download_items_from_database_to_storages(
        config: cfg.DownloaderConfig,
        database: db.Database,
        output: out.Output,
) -> list[action_class.Action]:
    """Do the actual download job."""
    # TODO - add logic here
    return []
