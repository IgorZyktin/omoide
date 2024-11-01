"""Execution tools for serial operations."""

import abc

from omoide import custom_logging
from omoide import models
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class SerialOperationImplementation(abc.ABC):
    """Base class for operation implementations."""

    def __init__(
        self,
        operation: models.SerialOperation,
        config: Config,
        mediator: WorkerMediator,
    ) -> None:
        """Initialize instance."""
        self.operation = operation
        self.config = config
        self.mediator = mediator

    @abc.abstractmethod
    async def execute(self) -> None:
        """Perform workload."""
