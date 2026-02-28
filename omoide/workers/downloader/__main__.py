"""Worker that downloads media files."""

import os
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import nano_settings as ns

from omoide import custom_logging
from omoide.infra.implementations.prometheus_metric_collector import (
    PrometheusMetricsCollector,
)
from omoide.infra.interfaces.abs_metrics_collector import Metric
from omoide.workers.downloader.cfg import WorkerDownloaderConfig
from omoide.workers.downloader.database import DownloaderPostgreSQLDatabase
from omoide.workers.downloader import operations

LOG = custom_logging.get_logger(__name__)
WORKING = threading.Event()
WORKING.set()

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
    LOG.warning(
        'Received signal {signame} ({signum}). Shutting down gracefully...',
        signame=signal.strsignal(signum),
        signum=signum,
    )
    WORKING.clear()


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

    cores = config.workers or os.cpu_count() or 1
    cores = min(cores, config.max_workers)
    executor = ThreadPoolExecutor(max_workers=cores)

    try:
        while WORKING.is_set():
            submitted = 0
            try:
                candidates = database.get_media_candidates(
                    batch_size=config.input_batch
                )

                for target_id in candidates:
                    took_lock = database.lock(target_id, config.name)

                    if not took_lock:
                        continue

                    executor.submit(
                        do_download, config, database, metrics, target_id
                    )
                    submitted += 1
            except Exception:
                LOG.exception('Failed to perform work cycle')
                time.sleep(config.exc_delay)

            if submitted:
                time.sleep(config.short_delay)
            else:
                time.sleep(config.long_delay)
    finally:
        database.disconnect()
        metrics.stop()
        executor.shutdown()

    LOG.info('Stopped downloader worker: {}', config.name)


def do_download(
    config: WorkerDownloaderConfig,
    database: DownloaderPostgreSQLDatabase,
    metrics: PrometheusMetricsCollector,
    target_id: int,
) -> None:
    """Actually download a media."""
    try:
        model = database.load_media(target_id)
        operations.download_media(config, database, model)
    except Exception:
        traceback = custom_logging.capture_exception_output(
            'Failed to perform download'
        )
        database.mark_failed_and_release_lock(
            target_id, error=traceback or '???'
        )
        LOG.exception('Failed to download output media {}', target_id)
        metrics.increment(M_ERRORS, 1)
    else:
        LOG.info('Downloaded output media {}', target_id)
        database.delete_media(target_id)
        metrics.increment(M_FILES_PROCESSED, 1)
        metrics.increment(M_BYTES_PROCESSED, len(model.content))
        del model


if __name__ == '__main__':
    main()
