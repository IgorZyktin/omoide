"""Worker that performs operations one by one."""

from omoide import custom_logging
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.serial.cfg import Config
from omoide.workers.serial.database import SerialDatabase

LOG = custom_logging.get_logger(__name__)


class SerialWorker(BaseWorker[Config, SerialDatabase]):
    """Worker that performs operations one by one."""

    def __init__(self, config: Config, db: SerialDatabase) -> None:
        """Initialize instance."""
        super().__init__(config, db)
        self.has_lock = False

    async def execute(self) -> bool:
        """Perform workload."""
        if not self.has_lock:
            lock = await self.db.take_lock()

            if not lock:
                return False

            LOG.info('Worker {} took lock', self.config.name)
            self.has_lock = True

        operation = await self.db.get_next_operation()

        if not operation:
            return False

        done_something = False
        try:
            LOG.info('Executing operation {} {}', operation.id, operation.name)
            done_something = await operation.execute()
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
            await self.db.fail_operation(operation, error=error)
            LOG.exception(
                'Operation {} {} failed', operation.id, operation.name
            )
        else:
            await self.db.complete_operation(operation)
            LOG.info('Operation {} {} complete', operation.id, operation.name)

        return done_something

    async def stop(self) -> None:
        """Start worker."""
        lock = await self.db.release_lock()
        if lock:
            LOG.info('Worker {} released lock', self.config.name)
        await super().stop()
