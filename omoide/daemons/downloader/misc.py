# -*- coding: utf-8 -*-
"""Miscellaneous tools for downloader.
"""
from types import FunctionType

import click

from omoide.daemons.common import out
from omoide.daemons.downloader import cfg

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


def get_output_instance_for_downloader(
        config: cfg.DownloaderConfig,
) -> out.Output:
    """Perform basic setup for the output."""
    output = out.Output(silent=config.silent)

    output.add_columns(
        out.Column(name='Processed at', width=27, alias='processed_at'),
        out.Column(name='UUID', width=38, alias='uuid'),
        out.Column(name='Type', width=11, alias='type'),
        out.Column(name='Size', width=14, alias='size'),
        out.Column(name='Status', width=8, alias='status'),
        out.Column(name='Location', width=95, alias='location'),
    )

    return output
