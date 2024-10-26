"""Worker that performs operations one by one."""

from omoide import custom_logging
from omoide import utils
from omoide.serial_operations import SerialOperation
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import operations as op
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

    async def execute_operation(self, operation: SerialOperation) -> None:
        """Perform workload."""
        try:
            executor = op.SerialOperationExecutor.from_operation(
                operation=operation,
                config=self.config,
                mediator=self.mediator,
            )
            await executor.execute()
        except Exception as exc:
            error = utils.exc_to_str(exc)
            async with self.mediator.database.transaction() as conn:
                await self.mediator.workers.mark_serial_operation_failed(
                    conn, operation, error
                )
                LOG.exception(
                    'Operation {num}. `{goal}`, '
                    'failed in {duration:0.3f} sec. because of {error}',
                    num=operation.id,
                    operation=operation.goal.title(),
                    duration=operation.duration,
                    error=error,
                )
        else:
            async with self.mediator.database.transaction() as conn:
                await self.mediator.workers.mark_serial_operation_done(
                    conn, operation
                )
                LOG.info(
                    'Operation {num}. `{goal}`, '
                    'completed in {duration:0.3f} sec.',
                    num=operation.id,
                    operation=operation.goal.title(),
                    duration=operation.duration,
                )
