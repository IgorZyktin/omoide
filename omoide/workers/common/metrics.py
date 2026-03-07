"""Worker metrics."""

from omoide.infra.implementations.prometheus_metric_collector import PrometheusMetricsCollector
from omoide.infra.interfaces.abs_metrics_collector import Metric

FILES_PROCESSED = Metric(
    id=1,
    name='ow_files_processed',
    documentation='How many files we processed',
)
BYTES_PROCESSED = Metric(
    id=2,
    name='ow_bytes_processed',
    documentation='How many bytes we processed',
)
ERRORS = Metric(
    id=3,
    name='ow_errors',
    documentation='How many errors we got',
)
TIME_SPENT = Metric(
    id=4,
    name='ow_time_spent',
    documentation='How many seconds we spent processing data',
)


def get_metric_collector(
    address: str,
    port: int,
    name: str,
    worker_type: str,
) -> PrometheusMetricsCollector:
    """Return collector instance."""
    return PrometheusMetricsCollector(
        metrics=[
            FILES_PROCESSED,
            BYTES_PROCESSED,
            ERRORS,
            TIME_SPENT,
        ],
        address=address,
        port=port,
        labels={
            'name': name,
            'worker_type': worker_type,
        },
    )
