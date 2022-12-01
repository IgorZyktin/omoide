# -*- coding: utf-8 -*-
"""Omoide daemon that saves files to the filesystem.
"""
import time

import click
from pydantic import SecretStr

from omoide.daemons.worker import cfg
from omoide.infra import custom_logging


@click.command()
@click.option(
    '--name',
    type=str,
    help='Name of the worker instance (used for replication check)',
)
@click.option(
    '--db-url',
    type=str,
    help='Database URL',
)
@click.option(
    '--hot-folder',
    type=str,
    default='',
    help='Location of the hot folder (optional)',
    show_default=True,
)
@click.option(
    '--cold-folder',
    type=str,
    default='',
    help='Location of the cold folder (optional)',
    show_default=True,
)
@click.option(
    '--save-hot/--no-save-hot',
    type=bool,
    default=False,
    help='Save incoming data to the hot folder',
    show_default=True,
)
@click.option(
    '--save-cold/--no-save-cold',
    type=bool,
    default=False,
    help='Save incoming data to the cold folder',
    show_default=True,
)
@click.option(
    '--drop-after-saving/--no-drop-after-saving',
    default=False,
    help='Drop input row from the database after all workers are saved it',
    show_default=True,
)
@click.option(
    '--min-interval',
    type=int,
    default=5,
    help='Minimum amount of seconds between database checks',
    show_default=True,
)
@click.option(
    '--max-interval',
    type=int,
    default=300,
    help='Maximum amount of seconds between database checks',
    show_default=True,
)
@click.option(
    '--warm-up-coefficient',
    type=float,
    default=3.0,
    help='Multiply waiting interval by this coefficient after download',
    show_default=True,
)
@click.option(
    '--batch-size',
    type=int,
    default=50,
    help='Process this amount of items at one run',
    show_default=True,
)
@click.option(
    '--log-level',
    type=click.Choice([
        'DEBUG',
        'INFO',
        'WARNING',
        'CRITICAL',
        'ERROR',
        'NOTSET',
    ], case_sensitive=False),
    default='INFO',
    help='Log level of the worker',
    show_default=True,
)
def main(**kwargs):
    """Entry point."""
    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)

    custom_logging.init_logging(config.log_level)
    logger = custom_logging.get_logger(__name__)
    logger.info('Started Omoide Worker daemon')
    logger.info('\nConfig:\n\t{}', config.verbose())

    try:
        _run(config)
    except KeyboardInterrupt:
        logger.warning('Worker was manually stopped')


def _run(config: cfg.Config):
    """Actual execution start."""
    _ = config

    while True:
        time.sleep(1)
        # TODO


if __name__ == '__main__':
    main()
