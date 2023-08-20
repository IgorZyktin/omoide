"""Daemon that saves files to the filesystem.
"""
import sys

import click

from omoide.daemons.worker import interfaces
from omoide.daemons.worker import worker_config
from omoide.daemons.worker.database import Database
from omoide.daemons.worker.filesystem import Filesystem
from omoide.daemons.worker.worker import Worker
from omoide.infra import custom_logging

_config = worker_config.get_config()
custom_logging.init_logging(_config.log_level, diagnose=_config.log_debug)
LOG = custom_logging.get_logger(__name__)


@click.option(
    '--once/--forever',
    type=bool,
    default=False,
    help='Run once and then stop',
    show_default=True,
)
def main(once: bool):
    """Entry point."""
    config = worker_config.get_config()
    LOG.info('Started Omoide Worker daemon: {}', config.name)
    LOG.info('\nConfig:\n{}', worker_config.serialize(config))

    worker = Worker(
        config=config,
        database=Database(db_url=config.db_url.get_secret_value()),
        filesystem=Filesystem(),
    )

    try:
        with LOG.catch():
            if once:
                run_once(config, worker)
            else:
                strategy = get_strategy(config)
                run_forever(config, worker, strategy)
    except KeyboardInterrupt:
        LOG.warning('Worker {} was manually stopped', config.name)


def get_strategy(config: worker_config.Config) -> interfaces.AbsStrategy:
    """Return instance of current strategy."""
    if sys.platform == 'win32':
        config_value = 'TimerStrategy'
    else:
        config_value = config.strategy

    match config_value:
        case 'SignalStrategy':
            from omoide.daemons.worker.strategies import by_signal
            strategy = by_signal.SignalStrategy()
        case 'TimerStrategy':
            from omoide.daemons.worker.strategies import by_timer
            strategy = by_timer.TimerStrategy(
                min_interval=config.timer_strategy.min_interval,
                max_interval=config.timer_strategy.max_interval,
                warm_up_coefficient=config.timer_strategy.warm_up_coefficient,
            )
        case _:
            msg = f'Unknown strategy: {config.strategy}'
            raise RuntimeError(msg)

    return strategy


def run_once(
        config: worker_config.Config,
        worker: Worker,
) -> None:
    """Perform one cycle (expected to be launched manually)."""
    with worker.database.life_cycle(echo=config.echo):
        perform_one_work_cycle(config, worker)


def run_forever(
        config: worker_config.Config,
        worker: Worker,
        strategy: interfaces.AbsStrategy,
) -> None:
    """Indefinitely repeat cycles."""
    # with worker.database.life_cycle(echo=worker.config.echo):
    #     while True:
    #         # noinspection PyBroadException
    #         try:
    #             operations = do_stuff(logger, database, worker)
    #         except Exception:
    #             operations = 0
    #             logger.exception('Failed to execute worker operation!')
    #
    #         worker.adjust_interval(operations)
    #         logger.debug('Sleeping for {:0.3f} seconds after {} operations',
    #                      worker.sleep_interval, operations)
    #
    #         if worker.config.single_run:
    #             break
    #
    #         time.sleep(worker.sleep_interval)


def perform_one_work_cycle(
        config: worker_config.Config,
        worker: interfaces.AbsWorker,
) -> None:
    """Perform all worker related duties."""
    if config.media.should_process:
        worker.download_media()

        if config.media.drop_after and config.media.replication_formula:
            worker.drop_media()

    if config.manual_copy.should_process:
        worker.manual_copy()

        if config.manual_copy.drop_after:
            worker.drop_manual_copies()


if __name__ == '__main__':
    main()  # pragma: no cover
