"""Common use case elements for workers."""

from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import SerialWorkerConfig


class BaseSerialWorkerUseCase:
    """Base use case class for workers."""

    def __init__(self, config: SerialWorkerConfig, mediator: WorkerMediator) -> None:
        """Initialize instance."""
        self.config = config
        self.mediator = mediator
