"""Use cases for item introduction."""

from omoide import custom_logging
from omoide import operations
from omoide.workers.serial.use_cases.base_use_case import BaseSerialWorkerUseCase

LOG = custom_logging.get_logger(__name__)


class IntroduceItemUseCase(BaseSerialWorkerUseCase):
    """Use case for introducing an item."""

    async def execute(self, operation: operations.RebuildPermissionsForItemOp) -> None:
        """Perform workload."""
        # TODO
        #  1. Resize the item
        #  2. Calculate signatures
