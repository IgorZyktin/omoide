"""Worker that converts media files."""

import os
import signal
import time

import nano_settings as ns

from omoide import custom_logging
from omoide.workers.converter import conversions
from omoide.workers.converter import dependencies as dep
from omoide.workers.converter.cfg import WorkerConverterConfig
from omoide.workers.converter.interfaces import AbsStorage

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

    storage = dep.get_storage(
        url=config.db.url.get_secret_value(),
        echo=config.db.echo,
    )

    while WORKING:
        try:
            done_something = do_work(config, storage)
        except Exception:
            LOG.exception('Failed to perform work cycle')
            time.sleep(config.exc_delay)
        else:
            if done_something:
                time.sleep(config.short_delay)
            else:
                time.sleep(config.long_delay)

    LOG.info('Stopped converter worker: {}', config.name)


def do_work(config: WorkerConverterConfig, storage: AbsStorage) -> bool:
    """Perform workload."""
    candidates = storage.get_candidates(config.input_batch)
    for target_id in candidates:
        took_lock = storage.lock(target_id)

        if not took_lock:
            continue

        model = storage.load_model(target_id)

        if not model:
            continue

        converter = conversions.CONVERTERS.get(model.content_type.lower())

        if converter is None:
            message = f'Unknown content type: {model.content_type!r}'
            storage.mark_failed_and_release_lock(target_id, error=message)
            continue

        try:
            converter(config, storage, model)
        except Exception:
            traceback = custom_logging.capture_exception_output('Failed to perform conversion')
            storage.mark_failed_and_release_lock(target_id, error=traceback)
            return False
        else:
            storage.delete(target_id)
            del model
            return True

    return False


if __name__ == '__main__':
    main()
