"""Worker that performs operations in parallel."""

import asyncio
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
import time

from omoide import custom_logging
from omoide import exceptions
from omoide import operations
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.parallel.cfg import ParallelWorkerConfig
from omoide.workers.parallel.use_cases.mapping import NAMES_TO_USE_CASES

LOG = custom_logging.get_logger(__name__)


class ParallelWorker(BaseWorker):
    """Worker that performs operations in parallel."""

    def __init__(
        self,
        config: ParallelWorkerConfig,
        mediator: WorkerMediator,
        name: str,
        executor: ProcessPoolExecutor | ThreadPoolExecutor,
    ) -> None:
        """Initialize instance."""
        super().__init__(mediator, name)
        self.config = config
        self.executor = executor

    async def stop(self) -> None:
        """Stop worker."""
        self.executor.shutdown()
        await super().stop()

    async def execute(self) -> bool:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            batch = await self.mediator.workers.get_next_parallel_batch(
                conn=conn,
                worker_name=self.config.name,
                names=self.config.supported_operations,
                batch_size=self.config.input_batch,
            )

        if not batch:
            return False

        await self.execute_batch(batch)
        return True

    async def execute_batch(self, batch: list[operations.BaseParallelOperation]) -> None:
        """Perform workload."""
        for operation in batch:
            try:
                use_case_type = NAMES_TO_USE_CASES.get(operation.name)

                if use_case_type is None:
                    raise exceptions.UnknownParallelOperationError(name=operation.name)  # noqa: TRY301

                use_case = use_case_type(self.config, self.mediator)
                new_callable = await use_case.execute(operation)  # type: ignore [attr-defined]
                await self.run_callable(new_callable)
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
                operation.processed_by.add(self.name)
                async with self.mediator.database.transaction() as conn:
                    await self.mediator.workers.save_parallel_operation(conn, operation)

    async def run_callable(self, new_callable: Callable) -> None:
        """Run operation in separate thread/process."""
        deadline = time.monotonic() + self.config.operation_deadline
        future = self.executor.submit(new_callable)

        while True:
            if time.monotonic() > deadline:
                raise exceptions.BadParallelOperationError(
                    problem=f'running longer than {self.config.operation_deadline} sec',
                )

            if future.done():
                break

            await asyncio.sleep(self.config.operation_delay)

        _ = future.result()
