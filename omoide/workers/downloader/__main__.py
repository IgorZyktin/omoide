"""Worker that downloads media files."""

import os
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from omoide.workers import utils
from functools import partial
import nano_settings as ns
import python_utilz as pu

from omoide import custom_logging
from omoide.infra.implementations.prometheus_metric_collector import (
    PrometheusMetricsCollector,
)
from omoide.workers.downloader.cfg import WorkerDownloaderConfig
from omoide.workers.downloader.database import DownloaderPostgreSQLDatabase
from omoide.workers.downloader import operations
from omoide.workers.common import metrics as common_metrics

LOG = custom_logging.get_logger(__name__)
WORKING = threading.Event()
WORKING.set()


def main() -> None:
    """Entry point."""
    config = ns.from_env(
        WorkerDownloaderConfig,
        env_prefix='omoide_worker_downloader',
    )

    custom_logging.init_logging(
        level=config.log.level,
        diagnose=config.log.diagnose,
        path=config.log.path,
        rotation=config.log.rotation,
    )

    LOG.info('Started downloader worker: {}', config.name)

    signal_handler = partial(
        utils.signal_handler, event=WORKING, deadline=config.shutdown_deadline
    )
    signal.signal(signal.SIGINT, signal_handler)

    database = DownloaderPostgreSQLDatabase(
        url=config.db.url.get_secret_value(),
        echo=config.db.echo,
    )

    database.connect()
    metrics_collector = common_metrics.get_metric_collector(
        address=config.metrics.address,
        port=config.metrics.port,
        name=config.name,
        worker_type='downloader',
    )
    metrics_collector.start()

    cores = config.workers or os.cpu_count() or 1
    cores = min(cores, config.max_workers)
    executor = ThreadPoolExecutor(max_workers=cores)

    try:
        while WORKING.is_set():
            submitted = 0
            try:
                candidates = database.get_output_media_candidates(
                    batch_size=config.input_batch
                )

                for target_id in candidates:
                    took_lock = database.lock_output_media(
                        target_id, config.name
                    )

                    if not took_lock:
                        continue

                    executor.submit(
                        do_download,
                        config,
                        database,
                        metrics_collector,
                        target_id,
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
        metrics_collector.stop()
        executor.shutdown()

    LOG.info('Stopped downloader worker: {}', config.name)


def do_download(
    config: WorkerDownloaderConfig,
    database: DownloaderPostgreSQLDatabase,
    metrics_collector: PrometheusMetricsCollector,
    item_id: int,
) -> None:
    """Actually download a media."""
    model = database.get_output_media(item_id)
    oid = model.extras.get('oid')
    if oid:
        model.content = database.get_large_object(oid)

    try:
        start = time.perf_counter()
        operations.download_media(config, database, model)
        time_spent = time.perf_counter() - start
    except Exception:
        traceback = custom_logging.capture_exception_output(
            'Failed to perform download'
        )
        database.mark_failed_and_release_lock(
            item_id, error=traceback or '???'
        )
        LOG.exception(
            'Failed to download output {} for {}, {}',
            model.content_type,
            model.item_uuid,
            pu.human_readable_size(len(model.content)),
        )
        metrics_collector.increment(common_metrics.ERRORS, 1)
    else:
        LOG.info(
            'Downloaded output {} for {}, {}',
            model.content_type,
            model.item_uuid,
            pu.human_readable_size(len(model.content)),
        )
        metrics_collector.increment(common_metrics.FILES_PROCESSED, 1)
        metrics_collector.increment(
            common_metrics.BYTES_PROCESSED, len(model.content)
        )
        metrics_collector.increment(
            common_metrics.TIME_SPENT, int(time_spent * 1000)
        )
        if oid:
            database.delete_large_object(oid)
        database.delete_output_media(item_id)
        model.content = b''
        del model


if __name__ == '__main__':
    main()
