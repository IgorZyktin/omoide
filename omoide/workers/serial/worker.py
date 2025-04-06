"""Worker that performs operations one by one."""

import python_utilz as pu

from omoide import custom_logging
from omoide import models
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import operations
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class SerialWorker(BaseWorker[Config]):
    """Worker that performs operations one by one."""

    def __init__(self, config: Config, mediator: WorkerMediator) -> None:
        """Initialize instance."""
        super().__init__(config, mediator)
        self.has_lock = False

    async def stop(self) -> None:
        """Stop worker."""
        async with self.mediator.database.transaction() as conn:
            lock = await self.mediator.workers.release_serial_lock(
                conn=conn,
                worker_name=self.config.name,
            )

            if lock:
                LOG.info('Worker {!r} released lock', self.config.name)

        await super().stop()

    async def execute(self) -> bool:
        """Perform workload."""
        if not self.has_lock:
            async with self.mediator.database.transaction() as conn:
                lock = await self.mediator.workers.take_serial_lock(
                    conn=conn,
                    worker_name=self.config.name,
                )

            if not lock:
                return False

            LOG.info('Worker {!r} took serial lock', self.config.name)
            self.has_lock = True

        async with self.mediator.database.transaction() as conn:
            operation = await self.mediator.workers.get_next_serial_operation(
                conn=conn,
                names=self.config.supported_operations,
            )

        if not operation:
            return False

        async with self.mediator.database.transaction() as conn:
            locked = await self.mediator.workers.lock_serial_operation(
                conn=conn,
                operation=operation,
                worker_name=self.config.name,
            )

        if not locked:
            return False

        await self.execute_operation(operation)
        return True

    async def execute_operation(self, operation: models.SerialOperation) -> None:
        """Perform workload."""
        try:
            implementation = operations.get_implementation(
                config=self.config,
                operation=operation,
                mediator=self.mediator,
            )
            await implementation.execute()
        except Exception as exc:
            error = pu.exc_to_str(exc)
            now = pu.now()
            operation.updated_at = now
            operation.ended_at = now
            operation.add_to_log(error)
            operation.status = models.OperationStatus.FAILED
            LOG.exception(
                '{operation} failed in {duration:0.3f} sec. because of {error}',
                operation=operation,
                duration=operation.duration,
                error=error,
            )
        else:
            now = pu.now()
            operation.updated_at = now
            operation.ended_at = now
            operation.status = models.OperationStatus.DONE

            if operation.duration > 1:
                duration = pu.human_readable_time(operation.duration)
            else:
                duration = '{duration:0.3f} sec.'.format(duration=operation.duration)

            LOG.info(
                '{operation} completed in {duration}',
                operation=operation,
                duration=duration,
            )
        finally:
            async with self.mediator.database.transaction() as conn:
                await self.mediator.workers.save_serial_operation(conn, operation)
