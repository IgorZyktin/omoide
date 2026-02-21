"""Worker that downloads media files."""

import os
import signal
import time
from typing import Any

import nano_settings as ns

from omoide import custom_logging
from omoide.infra.implementations.prometheus_metric_collector import (
    PrometheusMetricsCollector,
)
from omoide.infra.interfaces.abs_metrics_collector import Metric
from omoide.workers.converter import conversions
from omoide.workers.downloader.cfg import WorkerDownloaderConfig
from omoide.workers.downloader.database import DownloaderPostgreSQLDatabase

LOG = custom_logging.get_logger(__name__)
WORKING = True

M_FILES_PROCESSED = Metric(
    id=1,
    name='wd_files_processed',
    documentation='How many files we processed',
)

M_BYTES_PROCESSED = Metric(
    id=2,
    name='wd_bytes_processed',
    documentation='How many bytes we processed',
)

M_ERRORS = Metric(
    id=3,
    name='wd_errors',
    documentation='How many errors we got',
)


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
        WorkerDownloaderConfig,
        env_prefix='omoide_worker_downloader',
    )
    os.environ.clear()

    custom_logging.init_logging(
        level=config.log.level,
        diagnose=config.log.diagnose,
        path=config.log.path,
        rotation=config.log.rotation,
    )

    LOG.info('Started downloader worker: {}', config.name)

    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C

    database = DownloaderPostgreSQLDatabase(
        url=config.db.url.get_secret_value(),
        echo=config.db.echo,
    )

    metrics = PrometheusMetricsCollector(
        metrics=[M_FILES_PROCESSED, M_BYTES_PROCESSED, M_ERRORS],
        address=config.metrics.address,
        port=config.metrics.port,
        labels={
            'name': config.name,
        },
    )

    database.connect()
    metrics.start()

    while WORKING:
        try:
            done_something = do_work(config, database, metrics)
        except Exception:
            LOG.exception('Failed to perform work cycle')
            time.sleep(config.exc_delay)
        else:
            if done_something:
                time.sleep(config.short_delay)
            else:
                time.sleep(config.long_delay)

    database.disconnect()
    metrics.stop()

    LOG.info('Stopped downloader worker: {}', config.name)


def do_work(
    config: WorkerDownloaderConfig,
    database: DownloaderPostgreSQLDatabase,
    metrics: PrometheusMetricsCollector,
) -> bool:
    """Perform workload."""
    candidates = database.get_media_candidates(
        batch_size=config.input_batch,
        content_types=conversions.SUPPORTED_CONTENT_TYPES,
    )

    for target_id in candidates:
        took_lock = database.lock(target_id, config.name)

        if not took_lock:
            continue

        try:
            model = database.load_media(target_id)
            # TODO
        except Exception:
            traceback = custom_logging.capture_exception_output(
                'Failed to perform download'
            )
            database.mark_failed_and_release_lock(
                target_id, error=traceback or '???'
            )
            LOG.exception('Failed to download output media {}', target_id)
            metrics.increment(M_ERRORS, 1)
            return False
        else:
            LOG.info('Downloaded input media {}', target_id)
            database.delete_media(target_id)
            metrics.increment(M_FILES_PROCESSED, 1)
            metrics.increment(M_BYTES_PROCESSED, len(model.content))
            del model
            return True

    return False


if __name__ == '__main__':
    main()
