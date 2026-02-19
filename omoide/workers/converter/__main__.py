"""Worker that convert media files."""

import os
import signal
import time

import nano_settings as ns

from omoide import custom_logging
from omoide.workers.converter.cfg import WorkerConverterConfig

LOG = custom_logging.get_logger(__name__)
WORKING = True


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    _ = frame
    global WORKING  # noqa: PLW0603
    LOG.warning(
        'Received signal {signame} ({signum}). Shutting down gracefully...',
        signame=signal.strsignal(signum),
        signum=signum,
    )
    WORKING = False


def main():
    """Entry point."""
    config = ns.from_env(
        WorkerConverterConfig,
        env_prefix='omoide_worker_converter',
    )
    os.environ.clear()

    custom_logging.init_logging(
        level=config.log.level,
        diagnose=config.log.diagnose,
        path=config.log.path,
        rotation=config.log.rotation,
    )

    LOG.info('Started converter worker: {}', config.name)

    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C

    while WORKING:
        done_something = do_work()

        if done_something:
            time.sleep(config.short_delay)
        else:
            time.sleep(config.long_delay)

    LOG.info('Stopped converter worker: {}', config.name)


def do_work() -> bool:
    """Perform workload."""
    time.sleep(1)
    return True


if __name__ == '__main__':
    main()
