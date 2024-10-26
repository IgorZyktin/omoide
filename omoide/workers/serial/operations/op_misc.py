"""All other types of executors."""

import asyncio

from omoide import custom_logging
from omoide import serial_operations as so
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import operations as op
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class DummyExecutor(op.SerialOperationExecutor[Config, WorkerMediator]):
    """Dummy executor."""

    operation: so.DummySO

    async def execute(self) -> None:
        """Perform workload."""
        count = self.operation.extras.get('count') or 0

        for i in range(count):
            LOG.info('Doing something, {}', i)
            await asyncio.sleep(1.0)
