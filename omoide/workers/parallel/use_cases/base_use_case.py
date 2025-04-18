"""Common use case elements for workers."""

from omoide.workers.parallel.cfg import ParallelWorkerConfig


class BaseParallelWorkerUseCase:
    """Base use case class for workers."""

    def __init__(self, config: ParallelWorkerConfig) -> None:
        """Initialize instance."""
        self.config = config
