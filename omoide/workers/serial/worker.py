"""Worker that performs operations one by one."""

from omoide import custom_logging
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.serial.cfg import Config
from omoide.workers.serial.database import SerialDatabase

LOG = custom_logging.get_logger(__name__)


class SerialWorker(BaseWorker[Config, SerialDatabase]):
    """Worker that performs operations one by one."""

    async def execute(self) -> bool:
        """Perform workload."""
        LOG.info('Doing something {}', self.config.name)
        return False
