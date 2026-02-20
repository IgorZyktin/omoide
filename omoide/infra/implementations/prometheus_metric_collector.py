"""Sender that interacts with prometheus using pull model."""

from collections.abc import Collection
from typing import TYPE_CHECKING

from prometheus_client import Counter, start_http_server

from omoide.infra.interfaces.abs_metrics_collector import AbsMetricsCollector
from omoide.infra.interfaces.abs_metrics_collector import Metric
from omoide import custom_logging

if TYPE_CHECKING:
    from threading import Thread  # pragma: no cover
    from wsgiref.simple_server import WSGIServer  # pragma: no cover

LOG = custom_logging.get_logger(__name__)


class PrometheusMetricsCollector(AbsMetricsCollector):
    """Sender that interacts with prometheus using pull model."""

    def __init__(  # noqa: PLR0913
        self,
        metrics: Collection[Metric],
        address: str,
        port: int,
        labels: dict[str, str],
    ) -> None:
        """Initialize instance."""
        self.address = address
        self.port = port
        self.labels = labels

        self._server: WSGIServer | None = None
        self._thread: Thread | None = None

        self._counter_metrics: dict[int, Counter] = {}

        for metric in metrics:
            match metric.type:
                case 'counter':
                    self._counter_metrics[metric.id] = Counter(
                        name=metric.name,
                        documentation=metric.documentation,
                        labelnames=self.labels.keys(),
                    )
                case _:
                    LOG.warning('Unknown metric type: {}', metric)

    def start(self) -> None:
        """Start HTTP server."""
        self._server, self._thread = start_http_server(self.port, addr=self.address)
        LOG.info('Prometheus server started on {}:{}', self.address, self.port)

    def stop(self) -> bool:
        """Prepare for exit."""
        did_something = False

        if self._server is not None:
            self._server.shutdown()
            self._server = None
            did_something = True

        if self._thread is not None:
            self._thread.join()
            self._thread = None
            did_something = True

        if did_something:
            LOG.info('Prometheus server stopped')

        return did_something

    def increment(
        self,
        metric: Metric,
        value: float = 1.0,
    ) -> None:
        """Increment value."""
        obj = self._counter_metrics.get(metric.id)

        if obj is None:
            LOG.error('Cannot increment unknown metric {}', metric)
            return

        try:
            obj.labels(**self.labels).inc(value)
        except Exception as exc:
            LOG.error(
                'Failed to increment metric {metric} because of {error}',
                metric=metric,
                error=exc,
            )
