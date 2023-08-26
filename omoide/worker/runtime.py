"""Worker runtime.
"""
import sys
import threading

from omoide.infra import custom_logging
from omoide.worker import interfaces
from omoide.worker import worker_config

LOG = custom_logging.get_logger(__name__)


def run_once(
        config: worker_config.Config,
        worker: interfaces.AbsWorker,
) -> None:
    """Perform one cycle (expected to be launched manually)."""
    with LOG.catch():
        perform_one_work_cycle(config, worker)


def run_forever(
        config: worker_config.Config,
        worker: interfaces.AbsWorker,
        strategy: interfaces.AbsStrategy,
) -> None:
    """Indefinitely repeat cycles."""
    strategy.init()

    executor = threading.Thread(
        target=execute,
        args=(config, worker, strategy),
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
        worker: interfaces.AbsWorker,
        strategy: interfaces.AbsStrategy,
) -> None:
    """Perform all worker related duties."""
    should_stop = False

    while not should_stop:
        operations_before = worker.counter
        # noinspection PyBroadException
        try:
            perform_one_work_cycle(config, worker)
        except Exception:
            LOG.exception('Failed to execute worker cycle')

        done_something = worker.counter > operations_before
        strategy.adjust(done_something)
        should_stop = strategy.wait()


def perform_one_work_cycle(
        config: worker_config.Config,
        worker: interfaces.AbsWorker,
) -> None:
    """Perform all worker related duties."""
    # if config.media.should_process:
    #     # worker.download_media()
    #
    #     if config.media.drop_after:
    #         worker.drop_media()

    if config.copy_thumbnails.should_process:
        worker.copy_thumbnails()

        if config.copy_thumbnails.drop_after:
            worker.drop_thumbnail_copies()


def get_strategy(config: worker_config.Config) -> interfaces.AbsStrategy:
    """Return instance of current strategy."""
    if sys.platform == 'win32':
        strategy_name = 'TimerStrategy'
        LOG.warning(
            'Backing off to {} while running on Windows',
            strategy_name,
        )
    else:
        strategy_name = config.strategy

    match strategy_name:
        case 'SignalStrategy':
            from omoide.worker.strategies import by_signal
            strategy = by_signal.SignalStrategy()

        case 'TimerStrategy':
            from omoide.worker.strategies import by_timer
            strategy = by_timer.TimerStrategy(
                min_interval=config.timer_strategy.min_interval,
                max_interval=config.timer_strategy.max_interval,
                warm_up_coefficient=config.timer_strategy.warm_up_coefficient,
            )

        case _:
            msg = f'Unknown strategy: {strategy_name}'
            raise RuntimeError(msg)

    return strategy
