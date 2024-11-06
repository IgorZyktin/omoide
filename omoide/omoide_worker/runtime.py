"""Worker runtime."""

import threading

from omoide import custom_logging
from omoide.omoide_worker import interfaces
from omoide.omoide_worker import worker_config
from omoide.omoide_worker.strategies import by_timer

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
        strategy.adjust(done_something=done_something)
        should_stop = strategy.wait()


def perform_one_work_cycle(
    config: worker_config.Config,
    worker: interfaces.AbsWorker,
) -> None:
    """Perform all worker related duties."""
    if config.media.should_process:
        worker.download_media()

    if config.media.drop_after:
        worker.drop_media()

    if config.copy_commands.should_process:
        worker.copy()

    if config.copy_commands.drop_after:
        worker.drop_copies()


def get_strategy(config: worker_config.Config) -> interfaces.AbsStrategy:
    """Return instance of current strategy."""
    return by_timer.TimerStrategy(
        min_interval=config.timer_strategy.min_interval,
        max_interval=config.timer_strategy.max_interval,
        warm_up_coefficient=config.timer_strategy.warm_up_coefficient,
    )
