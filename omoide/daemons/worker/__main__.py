# -*- coding: utf-8 -*-
"""Omoide daemon that saves files to the filesystem.
"""
import time

import click
import ujson
from pydantic import SecretStr

from omoide.daemons.worker import cfg
from omoide.daemons.worker.db import Database
from omoide.daemons.worker.filesystem import Filesystem
from omoide.daemons.worker.worker import Worker
from omoide.infra import custom_logging


@click.command()
@click.option(
    '--name',
    required=True,
    type=str,
    help='Name of the worker instance (used for replication check)',
)
@click.option(
    '--db-url',
    required=True,
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
    '--download-media/--no-download-media',
    default=False,
    help='Download media from the database to the filesystem',
    show_default=True,
)
@click.option(
    '--manual-copy/--no-manual-copy',
    default=False,
    help='Copy data between items',
    show_default=True,
)
@click.option(
    '--drop-done-media/--no-drop-done-media',
    default=False,
    help='Drop media row from the database after all workers are saved it',
    show_default=True,
)
@click.option(
    '--drop-done-copies/--no-drop-done-copies',
    default=False,
    help='Drop manual copy requests after uploading',
    show_default=True,
)
@click.option(
    '--min-interval',
    type=float,
    default=0.1,
    help='Minimum amount of seconds between database checks',
    show_default=True,
)
@click.option(
    '--max-interval',
    type=float,
    default=300.0,
    help='Maximum amount of seconds between database checks',
    show_default=True,
)
@click.option(
    '--warm-up-coefficient',
    type=float,
    default=1.3,
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
@click.option(
    '--debug/--no-debug',
    type=bool,
    default=False,
    help='Shows verbose stack trace on exceptions',
    show_default=True,
)
@click.option(
    '--prefix-size',
    type=int,
    default=2,
    help='Amount of symbols from UUID to form bucket',
    show_default=True,
)
@click.option(
    '--single-run/--no-single-run',
    type=bool,
    default=False,
    help='Run once and then stop',
    show_default=True,
)
@click.option(
    '--echo/--no-echo',
    type=bool,
    default=False,
    help='Verbose output of database operations',
    show_default=True,
)
@click.option(
    '--replication-formula',
    type=str,
    default='{}',
    help='Can delete media after its replication state goes into this (JSON)',
    show_default=True,
)
def main(**kwargs):
    """Entry point."""
    db_url = SecretStr(kwargs.pop('db_url'))
    replication_formula = ujson.loads(kwargs.pop('replication_formula'))
    config = cfg.Config(
        db_url=db_url,
        replication_formula=replication_formula,
        **kwargs,
    )

    custom_logging.init_logging(config.log_level, diagnose=config.debug)
    logger = custom_logging.get_logger(__name__)
    logger.info('Started Omoide Worker daemon')
    logger.info('\nConfig:\n\t{}', config.verbose())

    database = Database(db_url=config.db_url.get_secret_value())
    worker = Worker(config=config, filesystem=Filesystem())

    try:
        with logger.catch():
            run(logger, database, worker)
    except KeyboardInterrupt:
        logger.warning('Worker was manually stopped')


def run(
        logger: custom_logging.Logger,
        database: Database,
        worker: Worker,
) -> None:
    """Actual execution start."""
    with database.life_cycle(echo=worker.config.echo):
        while True:
            # noinspection PyBroadException
            try:
                operations = do_stuff(logger, database, worker)
            except Exception:
                operations = 0
                logger.exception('Failed to execute worker operation!')

            worker.adjust_interval(operations)
            logger.debug('Sleeping for {:0.3f} seconds after {} operations',
                         worker.sleep_interval, operations)

            if worker.config.single_run:
                break

            time.sleep(worker.sleep_interval)


def do_stuff(
        logger: custom_logging.Logger,
        database: Database,
        worker: Worker,
) -> int:
    """Perform all worker related duties."""

    def _maybe_save(key: str, value: int) -> None:
        if value:
            database.save_statistic(key=key, value=done)

    operations = 0

    if worker.config.download_media:
        done = worker.download_media(logger, database)
        operations += done
        _maybe_save(f'worker-save-media-{worker.config.name}', done)

        if worker.config.drop_done_media and worker.config.replication_formula:
            done = worker.drop_media(logger, database)
            operations += done
            _maybe_save(f'worker-drop-media-{worker.config.name}', done)

    if worker.config.manual_copy:
        done = worker.manual_copy(logger, database)
        operations += done
        _maybe_save(f'worker-save-copy-{worker.config.name}', done)

        if worker.config.drop_done_copies:
            done = worker.drop_manual_copies(logger, database)
            operations += done
            _maybe_save(f'worker-drop-copy-{worker.config.name}', done)

    return operations


if __name__ == '__main__':
    main()  # pragma: no cover
