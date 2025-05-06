"""Common use case elements for workers."""

from omoide.workers.serial.cfg import SerialWorkerConfig
from omoide.workers.serial.mediator import SerialWorkerMediator


class BaseSerialWorkerUseCase:
    """Base use case class for workers."""

    def __init__(self, config: SerialWorkerConfig, mediator: SerialWorkerMediator) -> None:
        """Initialize instance."""
        self.config = config
        self.mediator = mediator
