"""Class that does actual work for serial operations."""

import python_utilz as pu

from omoide import custom_logging
from omoide import exceptions
from omoide import operations
from omoide.workers.serial.cfg import SerialWorkerConfig
from omoide.workers.serial.mediator import SerialWorkerMediator
from omoide.workers.serial.use_cases.mapping import NAMES_TO_USE_CASES

LOG = custom_logging.get_logger(__name__)


class SerialOperationsProcessor:
    """Class that does actual work for serial operations."""

    def __init__(self, config: SerialWorkerConfig, mediator: SerialWorkerMediator) -> None:
        """Initialize instance."""
        self.config = config
        self.mediator = mediator
        self.has_lock = False

    async def __call__(self) -> bool:
        """Run one cycle."""
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

        skip: set[int] = set()
        for _ in range(self.config.input_batch):
            async with self.mediator.database.transaction() as conn:
                operation = await self.mediator.workers.get_next_serial_operation(
                    conn=conn,
                    names=self.config.supported_operations,
                    skip=skip,
                )

            if not operation:
                return False

            async with self.mediator.database.transaction() as conn:
                locked = await self.mediator.workers.lock_serial_operation(conn, operation)

            if locked:
                break

            skip.add(operation.id)

        return await self.execute_operation(operation)

    async def execute_operation(self, operation: operations.Operation) -> bool:
        """Perform workload."""
        LOG.info(
            '{operation} started',
            operation=operation,
            duration=operation.hr_duration,
        )

        use_case_type = NAMES_TO_USE_CASES.get(operation.name)
        if use_case_type is None:
            raise exceptions.UnknownSerialOperationError(name=operation.name)  # noqa: TRY301

        async with self.mediator.database.transaction() as conn:
            try:
                await self.mediator.workers.save_serial_operation_as_started(conn, operation)
                use_case = use_case_type(self.config, self.mediator)
                await use_case.execute(operation)
            except Exception as exc:
                error = pu.exc_to_str(exc)
                LOG.exception(
                    '{operation} failed in {duration} because of {error}',
                    operation=operation,
                    duration=operation.hr_duration,
                    error=error,
                )
                await self.mediator.workers.save_serial_operation_as_failed(
                    conn=conn,
                    operation=operation,
                    error=error,
                )
            else:
                LOG.info(
                    '{operation} completed in {duration}',
                    operation=operation,
                    duration=operation.hr_duration,
                )
                await self.mediator.workers.save_serial_operation_as_completed(
                    conn=conn,
                    operation=operation,
                    processed_by=self.config.name,
                )

        return True
