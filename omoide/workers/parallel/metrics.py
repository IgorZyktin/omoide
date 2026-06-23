"""Metrics for parallel workers."""

from omoide.infra.implementations.prometheus_metric_collector import (
    PrometheusMetricsCollector,
)
from omoide.infra.interfaces.abs_metrics_collector import Metric

COMMANDS_PROCESSED = Metric(
    id=1,
    name='owp_tasks_processed',
    documentation='How many commands we processed',
)
BYTES_PROCESSED = Metric(
    id=2,
    name='owp_bytes_processed',
    documentation='How many bytes we processed',
)
ERRORS = Metric(
    id=3,
    name='owp_errors',
    documentation='How many errors we got',
)
TIME_SPENT = Metric(
    id=4,
    name='owp_time_spent',
    documentation='How many seconds we spent during work',
)


def get_metric_collector(
    address: str,
    port: int,
    name: str,
) -> PrometheusMetricsCollector:
    """Return collector instance."""
    return PrometheusMetricsCollector(
        metrics=[
            COMMANDS_PROCESSED,
            BYTES_PROCESSED,
            ERRORS,
            TIME_SPENT,
        ],
        address=address,
        port=port,
        labels={'name': name},
    )
