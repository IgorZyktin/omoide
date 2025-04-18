"""Common use case elements for workers."""

import abc

from omoide import operations
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import SerialWorkerConfig


class BaseSerialWorkerUseCase(abc.ABC):
    """Base use case class for workers."""

    def __init__(self, config: SerialWorkerConfig, mediator: WorkerMediator) -> None:
        """Initialize instance."""
        self.config = config
        self.mediator = mediator

    @abc.abstractmethod
    async def execute(self, operation: operations.BaseSerialOperation) -> None:
        """Perform workload."""
