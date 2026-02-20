"""Interface for metric collection."""

import abc
from dataclasses import dataclass


@dataclass(frozen=True)
class Metric:
    """Basic info about metric."""

    id: int
    name: str
    documentation: str
    type: str = 'counter'


class AbsMetricsCollector(abc.ABC):
    """Abstract collector of metrics."""

    @abc.abstractmethod
    def start(self) -> None:
        """Prepare to work."""

    @abc.abstractmethod
    def stop(self) -> bool:
        """Prepare to exit."""

    @abc.abstractmethod
    def increment(
        self,
        metric: Metric,
        value: float = 1.0,
    ) -> None:
        """Increment value."""
