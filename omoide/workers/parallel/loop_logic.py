"""Class that does actual work for parallel operations."""

import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

import python_utilz as pu

from omoide import custom_logging
from omoide import models
from omoide import operations
from omoide.workers.parallel.cfg import ParallelWorkerConfig
from omoide.workers.parallel.mediator import ParallelWorkerMediator
from omoide.workers.parallel.use_cases.mapping import NAMES_TO_USE_CASES

LOG = custom_logging.get_logger(__name__)


class ParallelOperationsProcessor:
    """Class that does actual work for parallel operations."""

    def __init__(
        self,
        config: ParallelWorkerConfig,
        mediator: ParallelWorkerMediator,
        executor: ProcessPoolExecutor | ThreadPoolExecutor,
    ) -> None:
        """Initialize instance."""
        self.config = config
        self.mediator = mediator
        self.executor = executor

    async def __call__(self) -> bool:
        """Run one cycle."""
        async with self.mediator.database.transaction() as conn:
            batch = await self.mediator.workers.get_next_parallel_batch(
                conn=conn,
                worker_name=self.config.name,
                names=self.config.supported_operations,
                batch_size=self.config.input_batch,
            )

        if not batch:
            return False

        return await self.execute_batch(batch)

    async def execute_batch(self, batch: list[operations.Operation]) -> bool:
        """Perform workload."""
        did_something = False
        futures: dict[concurrent.futures.Future, operations.Operation] = {}

        for operation in batch:
            use_case_type = NAMES_TO_USE_CASES.get(operation.name)

            if use_case_type is None:
                LOG.error('Unknown parallel operation type: {!r}', operation.name)
                continue

            async with self.mediator.database.transaction() as conn:
                try:
                    use_case = use_case_type(self.config, self.mediator)
                    new_callable = await use_case.execute(operation)  # type: ignore [attr-defined]
                    future = self.executor.submit(new_callable)
                except Exception as exc:
                    error = pu.exc_to_str(exc)
                    LOG.exception(
                        'Failed operation after {duration} because of {error}: {operation}',
                        operation=operation,
                        duration=operation.hr_duration,
                        error=error,
                    )
                    await self.mediator.workers.save_parallel_operation_as_failed(
                        conn=conn,
                        operation=operation,
                        error=error,
                    )
                else:
                    futures[future] = operation
                    await self.mediator.workers.save_parallel_operation_as_started(
                        conn=conn,
                        operation=operation,
                    )

        for future in concurrent.futures.as_completed(futures):
            operation_after = futures.get(future)

            if operation_after is None:
                continue

            try:
                _ = future.result()
            except Exception as exc:
                error = pu.exc_to_str(exc)
                LOG.exception(
                    'Failed operation after {duration} because of {error}: {operation}',
                    operation=operation_after,
                    duration=operation_after.hr_duration.strip(),
                    error=error,
                )
                async with self.mediator.database.transaction() as conn:
                    await self.mediator.workers.save_parallel_operation_as_failed(
                        conn=conn,
                        operation=operation_after,
                        error=error,
                    )
            else:
                LOG.info(
                    'Finished operation in {duration}: {operation}',
                    operation=operation_after,
                    duration=operation_after.hr_duration.strip(),
                )
                async with self.mediator.database.transaction() as conn:
                    _, is_done = await self.mediator.workers.save_parallel_operation_as_complete(
                        conn=conn,
                        operation=operation_after,
                        minimal_completion=self.config.minimal_completion,
                        processed_by=self.config.name,
                    )

                    item_uuid = UUID(operation_after.extras['item_uuid'])
                    item = await self.mediator.items.get_by_uuid(conn, item_uuid)
                    item.status = models.Status.AVAILABLE
                    await self.mediator.items.save(conn, item)

                did_something = True

        return did_something
