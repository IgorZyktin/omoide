"""Worker that converts media files."""

import os
import signal
import threading
import time
from omoide.workers import utils
from functools import partial
import nano_settings as ns
import python_utilz as pu

from omoide import custom_logging
from omoide.infra.implementations.prometheus_metric_collector import (
    PrometheusMetricsCollector,
)
from omoide.workers.converter import conversions
from omoide.workers.converter.cfg import WorkerConverterConfig
from omoide.workers.converter.database import ConverterPostgreSQLDatabase
from omoide.workers.common import metrics as common_metrics

LOG = custom_logging.get_logger(__name__)
WORKING = threading.Event()
WORKING.set()


def main() -> None:
    """Entry point."""
    config = ns.from_env(
        WorkerConverterConfig,
        env_prefix='omoide_worker_converter',
    )

    custom_logging.init_logging(
        level=config.log.level,
        diagnose=config.log.diagnose,
        path=config.log.path,
        rotation=config.log.rotation,
    )

    LOG.info('Started converter worker: {}', config.name)

    signal_handler = partial(
        utils.signal_handler, event=WORKING, deadline=config.shutdown_deadline
    )
    signal.signal(signal.SIGINT, signal_handler)

    database = ConverterPostgreSQLDatabase(
        url=config.db.url.get_secret_value(),
        echo=config.db.echo,
    )

    metrics_collector = common_metrics.get_metric_collector(
        address=config.metrics.address,
        port=config.metrics.port,
        name=config.name,
        worker_type='converter',
    )

    os.makedirs(config.temp_folder, exist_ok=True)

    with metrics_collector, database:
        while WORKING.is_set():
            try:
                done_something = do_work(config, database, metrics_collector)
            except Exception:
                LOG.exception('Failed to perform work cycle')
                time.sleep(config.exc_delay)
            else:
                if done_something:
                    time.sleep(config.short_delay)
                else:
                    time.sleep(config.long_delay)

    LOG.info(
        'Worker {} stopped. Processed: {} files, {}, {} errors',
        config.name,
        pu.sep_digits(
            metrics_collector.get_value(common_metrics.FILES_PROCESSED)
        ),
        pu.human_readable_size(
            metrics_collector.get_value(common_metrics.BYTES_PROCESSED)
        ),
        pu.sep_digits(metrics_collector.get_value(common_metrics.ERRORS)),
    )


def do_work(
    config: WorkerConverterConfig,
    database: ConverterPostgreSQLDatabase,
    metrics_collector: PrometheusMetricsCollector,
) -> bool:
    """Perform workload."""
    candidates = database.get_input_media_candidates(
        batch_size=config.input_batch,
        content_types=conversions.SUPPORTED_CONTENT_TYPES,
    )

    for target_id in candidates:
        if not database.lock_input_media(target_id, config.name):
            continue

        model = database.get_input_media(target_id)
        oid = model.extras.pop('oid', None)
        if oid:
            model.content = database.get_large_object(oid)

        try:
            converter = conversions.CONVERTERS[model.content_type.lower()]
            start = time.perf_counter()
            converter(config, database, model)
            time_spent = time.perf_counter() - start
        except Exception:
            traceback = custom_logging.capture_exception_output(
                'Failed to perform conversion'
            )
            database.mark_failed_and_release_lock(
                target_id, error=traceback or '???'
            )
            LOG.exception(
                'Failed to convert input media {}, {}',
                model.item_uuid,
                pu.human_readable_size(len(model.content)),
            )
            metrics_collector.increment(common_metrics.ERRORS, 1)
            return False
        else:
            LOG.info(
                'Converted input media for {}, {}',
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
            database.delete_media(target_id)
            model.content = b''
            del model
            return True

    return False


if __name__ == '__main__':
    main()
