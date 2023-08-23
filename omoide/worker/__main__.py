"""Daemon that saves files to the filesystem.
"""
import sys
import threading

import click

from omoide.infra import custom_logging
from omoide.worker import interfaces
from omoide.worker import worker_config
from omoide.worker.database import Database
from omoide.worker.filesystem import Filesystem
from omoide.worker.worker import Worker

_config = worker_config.get_config()
custom_logging.init_logging(_config.log_level, diagnose=_config.log_debug)
LOG = custom_logging.get_logger(__name__)


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
    LOG.info('Started Omoide Worker Daemon')
    LOG.info('\nConfig:\n{}', worker_config.serialize(config))

    database = Database(
        db_url=config.db_uri.get_secret_value(),
        echo=config.db_echo,
    )

    worker = Worker(
        config=config,
        database=database,
        filesystem=Filesystem(),
    )

    if once:
        run_once(config, database, worker)
    else:
        strategy = get_strategy(config)
        run_forever(config, database, worker, strategy)


def run_once(
        config: worker_config.Config,
        database: Database,
        worker: interfaces.AbsWorker,
) -> None:
    """Perform one cycle (expected to be launched manually)."""
    with database.life_cycle():
        with LOG.catch():
            perform_one_work_cycle(config, worker)


def run_forever(
        config: worker_config.Config,
        database: Database,
        worker: Worker,
        strategy: interfaces.AbsStrategy,
) -> None:
    """Indefinitely repeat cycles."""
    strategy.start()

    executor = threading.Thread(
        target=execute,
        args=(config, database, worker, strategy),
    )

    executor.start()

    try:
        while True:
            executor.join()
            break
    except KeyboardInterrupt:
        LOG.warning('Worker was manually stopped')
        strategy.stop()


def execute(
        config: worker_config.Config,
        database: Database,
        worker: interfaces.AbsWorker,
        strategy: interfaces.AbsStrategy,
) -> None:
    """Perform all worker related duties."""
    with database.life_cycle():
        while True:
            should_stop = strategy.wait()

            if should_stop:
                break

            operations_before = worker.counter
            # noinspection PyBroadException
            try:
                perform_one_work_cycle(config, worker)
            except Exception:
                LOG.exception('Failed to execute worker operation!')

            done_something = worker.counter > operations_before
            strategy.adjust(done_something)


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


def get_strategy(config: worker_config.Config) -> interfaces.AbsStrategy:
    """Return instance of current strategy."""
    if sys.platform == 'win32':
        config_value = 'TimerStrategy'
    else:
        config_value = config.strategy

    match config_value:
        case 'SignalStrategy':
            from omoide.worker.strategies import by_signal
            strategy = by_signal.SignalStrategy(
                delay=config.signal_strategy.delay,
            )

        case 'TimerStrategy':
            from omoide.worker.strategies import by_timer
            strategy = by_timer.TimerStrategy(
                min_interval=config.timer_strategy.min_interval,
                max_interval=config.timer_strategy.max_interval,
                warm_up_coefficient=config.timer_strategy.warm_up_coefficient,
            )

        case _:
            msg = f'Unknown strategy: {config.strategy}'
            raise RuntimeError(msg)

    return strategy


if __name__ == '__main__':
    main()  # pragma: no cover
