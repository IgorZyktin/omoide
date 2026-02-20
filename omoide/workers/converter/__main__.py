"""Worker that converts media files."""

import os
import signal
import time
from typing import Any

import nano_settings as ns

from omoide import custom_logging
from omoide.workers.converter import conversions
from omoide.workers.converter import dependencies as dep
from omoide.workers.converter.cfg import WorkerConverterConfig
from omoide.workers.converter.interfaces import AbsDatabase

LOG = custom_logging.get_logger(__name__)
WORKING = True


def signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals."""
    _ = frame
    global WORKING  # noqa: PLW0603
    LOG.warning(
        'Received signal {signame} ({signum}). Shutting down gracefully...',
        signame=signal.strsignal(signum),
        signum=signum,
    )
    WORKING = False


def main() -> None:
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

    database = dep.get_database(
        url=config.db.url.get_secret_value(),
        echo=config.db.echo,
    )

    database.connect()

    while WORKING:
        try:
            done_something = do_work(config, database)
        except Exception:
            LOG.exception('Failed to perform work cycle')
            time.sleep(config.exc_delay)
        else:
            if done_something:
                time.sleep(config.short_delay)
            else:
                time.sleep(config.long_delay)

    database.disconnect()

    LOG.info('Stopped converter worker: {}', config.name)


def do_work(config: WorkerConverterConfig, database: AbsDatabase) -> bool:
    """Perform workload."""
    candidates = database.get_media_candidates(
        batch_size=config.input_batch,
        content_types=conversions.SUPPORTED_CONTENT_TYPES,
    )

    for target_id in candidates:
        took_lock = database.lock(target_id, config.name)

        if not took_lock:
            continue

        model = database.load_media(target_id)
        converter = conversions.CONVERTERS[model.content_type.lower()]

        try:
            converter(config, database, model)
        except Exception:
            traceback = custom_logging.capture_exception_output(
                'Failed to perform conversion'
            )
            database.mark_failed_and_release_lock(
                target_id, error=traceback or '???'
            )
            LOG.exception('Failed to convert input media {}', target_id)
            return False
        else:
            LOG.info('Converted input media {}', target_id)
            database.delete_media(target_id)
            del model
            return True

    return False


if __name__ == '__main__':
    main()
