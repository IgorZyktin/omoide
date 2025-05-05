"""Common use case elements for workers."""

from collections.abc import Callable

from omoide import operations
from omoide.workers.parallel.cfg import ParallelWorkerConfig
from omoide.workers.parallel.mediator import ParallelWorkerMediator


class BaseParallelWorkerUseCase:
    """Base use case class for workers."""

    def __init__(self, config: ParallelWorkerConfig, mediator: ParallelWorkerMediator) -> None:
        """Initialize instance."""
        self.config = config
        self.mediator = mediator

    async def execute(self, operation: operations.ParallelOperation) -> Callable:
        """Perform workload."""
