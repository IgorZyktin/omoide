"""Worker that performs operations one by one."""

from omoide import custom_logging
from omoide import exceptions
from omoide import operations
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import SerialWorkerConfig
from omoide.workers.serial.use_cases.mapping import NAMES_TO_USE_CASES

LOG = custom_logging.get_logger(__name__)


class SerialWorker(BaseWorker):
    """Worker that performs operations one by one."""

    def __init__(self, config: SerialWorkerConfig, mediator: WorkerMediator, name: str) -> None:
        """Initialize instance."""
        super().__init__(mediator, name)
        self.config = config
        self.has_lock = False

    async def stop(self) -> None:
        """Stop worker."""
        async with self.mediator.database.transaction() as conn:
            lock = await self.mediator.workers.release_serial_lock(
                conn=conn,
                worker_name=self.name,
            )

            if lock:
                LOG.info('Worker {!r} released lock', self.name)

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

    async def execute_operation(self, operation: operations.BaseSerialOperation) -> None:
        """Perform workload."""
        try:
            use_case_type = NAMES_TO_USE_CASES.get(operation.name)

            if use_case_type is None:
                raise exceptions.UnknownSerialOperationError(name=operation.name)  # noqa: TRY301

            use_case = use_case_type(operation)
            await use_case.execute(operation)
        except Exception as exc:
            error = operation.mark_failed(exc)
            LOG.exception(
                '{operation} failed in {duration} because of {error}',
                operation=operation,
                duration=operation.hr_duration,
                error=error,
            )
        else:
            operation.mark_done()
            LOG.info(
                '{operation} completed in {duration}',
                operation=operation,
                duration=operation.hr_duration,
            )
        finally:
            async with self.mediator.database.transaction() as conn:
                await self.mediator.workers.save_serial_operation(conn, operation)
