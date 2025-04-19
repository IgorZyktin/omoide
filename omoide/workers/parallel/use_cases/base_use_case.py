"""Common use case elements for workers."""

from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.parallel.cfg import ParallelWorkerConfig


class BaseParallelWorkerUseCase:
    """Base use case class for workers."""

    def __init__(self, config: ParallelWorkerConfig, mediator: WorkerMediator) -> None:
        """Initialize instance."""
        self.config = config
        self.mediator = mediator
