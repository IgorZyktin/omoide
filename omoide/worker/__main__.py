"""Daemon that saves files to the filesystem.
"""
import click

from omoide.infra import custom_logging
from omoide.worker import runtime
from omoide.worker import worker_config
from omoide.worker.database import Database
from omoide.worker.filesystem import Filesystem
from omoide.worker.worker import Worker


@click.command()
@click.option(
    '--once/--no-once',
    type=bool,
    default=False,
    help='Run once and then stop',
    show_default=True,
)
def main(once: bool):
    """Entry point."""
    config = worker_config.get_config()
    custom_logging.init_logging(config.log_level, diagnose=config.log_debug)

    logger = custom_logging.get_logger(__name__)
    logger.info('Started Omoide Worker Daemon')
    logger.info('\nConfig:\n{}', worker_config.serialize(config))

    database = Database(
        db_uri=config.db_uri.get_secret_value(),
        echo=config.db_echo,
    )

    filesystem = Filesystem(
        config=config,
    )

    worker = Worker(
        config=config,
        database=database,
        filesystem=filesystem,
    )

    with database.life_cycle():
        if once:
            runtime.run_once(config, worker)
        else:
            strategy = runtime.get_strategy(config)
            runtime.run_forever(config, worker, strategy)

    logger.info('Stopped Omoide Worker Daemon')


if __name__ == '__main__':
    main()  # pragma: no cover
