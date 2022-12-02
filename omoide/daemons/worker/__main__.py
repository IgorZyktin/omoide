# -*- coding: utf-8 -*-
"""Omoide daemon that saves files to the filesystem.
"""
import time

import click
from pydantic import SecretStr

from omoide.daemons.worker import cfg
from omoide.daemons.worker.db import Database
from omoide.daemons.worker.filesystem import Filesystem
from omoide.daemons.worker.worker import Worker
from omoide.infra import custom_logging
from omoide.infra.custom_logging import Logger


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
    '--media-downloading/--no-media-downloading',
    default=False,
    help='Download media from the database to the filesystem',
    show_default=True,
)
@click.option(
    '--filesystem-operations/--no-filesystem-operations',
    default=False,
    help='Perform scheduled operations with filesystem',
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
def main(**kwargs):
    """Entry point."""
    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)

    custom_logging.init_logging(config.log_level, diagnose=config.debug)
    logger = custom_logging.get_logger(__name__)
    logger.info('Started Omoide Worker daemon')
    logger.info('\nConfig:\n\t{}', config.verbose())

    database = Database(db_url=config.db_url.get_secret_value())
    worker = Worker(config=config, filesystem=Filesystem())

    try:
        with logger.catch():
            _run(logger, database, worker)
    except KeyboardInterrupt:
        logger.warning('Worker was manually stopped')


def _run(
        logger: custom_logging.Logger,
        database: Database,
        worker: Worker,
) -> None:
    """Actual execution start."""
    with database.life_cycle(echo=worker.config.echo):
        with database.start_session():
            meta_config = database.get_meta_config()

        while True:
            # noinspection PyBroadException
            try:
                did_something = _do_media_operations(
                    logger, database, worker, meta_config)

                did_something_else = _do_filesystem_operations(
                    logger, database, worker)

                did_something = did_something or did_something_else
            except Exception:
                logger.exception('Failed to execute worker operation!')
                did_something = False

            worker.adjust_interval(did_something)
            logger.debug('Sleeping for {:0.3f} seconds', worker.sleep_interval)

            if worker.config.single_run:
                break

            time.sleep(worker.sleep_interval)


def _do_media_operations(
        logger: Logger,
        database: Database,
        worker: Worker,
        meta_config: MetaConfig,
) -> bool:
    """Wrapper for media operations."""
    did_something = False
    did_something_else = False
    did_something_more = False

    if worker.config.media_downloading:
        did_something = worker.download_media(logger, database)

    if worker.config.drop_after_saving:
        if meta_config.replication_formula:
            logger.debug('Dropping all media that fits into formula: {}',
                         meta_config.replication_formula)
            did_something_else = worker.delete_media(
                logger=logger,
                database=database,
                replication_formula=meta_config.replication_formula,
            )

        if worker.config.filesystem_operations:
            did_something_more = worker.delete_filesystem_operations(
                logger=logger,
                database=database,
            )

    return (
            did_something
            or bool(did_something_else)
            or bool(did_something_more)
    )


def _do_filesystem_operations(
        logger: Logger,
        database: Database,
        worker: Worker,
) -> bool:
    """Wrapper for filesystem operations."""
    if worker.config.filesystem_operations:
        return worker.process_filesystem_operations(logger, database)
    return False


if __name__ == '__main__':
    main()
