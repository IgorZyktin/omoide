"""Worker that performs operations in parallel."""

import concurrent
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor

import python_utilz as pu

from omoide import custom_logging
from omoide import exceptions
from omoide import operations
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.parallel.cfg import ParallelWorkerConfig
from omoide.workers.parallel.use_cases.base_use_case import BaseParallelWorkerUseCase
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

    def get_use_case(
        self,
        operation: operations.BaseParallelOperation,
    ) -> BaseParallelWorkerUseCase:
        """Return use case."""
        use_case_type = NAMES_TO_USE_CASES.get(operation.name)

        if use_case_type is None:
            raise exceptions.UnknownParallelOperationError(name=operation.name)

        return use_case_type(self.config, self.mediator)

    async def execute_batch(self, batch: list[operations.BaseParallelOperation]) -> None:
        """Perform workload."""
        for operation in batch:
            try:
                use_case = self.get_use_case(operation)
                await self.run_callables(use_case, operation)
            except Exception as exc:
                error = pu.exc_to_str(exc)
                operation.add_to_log(error)
                operation.status = operations.OperationStatus.FAILED

                if operation.duration > 1:
                    duration = pu.human_readable_time(operation.duration)
                else:
                    duration = f'{operation.duration:0.3f} sec.'

                LOG.exception(
                    '{operation} failed in {duration} because of {error}',
                    operation=operation,
                    duration=duration,
                    error=error,
                )
            else:
                operation.status = operations.OperationStatus.DONE

                if operation.duration > 1:
                    duration = pu.human_readable_time(operation.duration)
                else:
                    duration = f'{operation.duration:0.3f} sec.'

                LOG.info(
                    '{operation} completed in {duration}',
                    operation=operation,
                    duration=duration,
                )
            finally:
                now = pu.now()
                operation.updated_at = now
                operation.ended_at = now
                operation.processed_by.add(self.name)
                async with self.mediator.database.transaction() as conn:
                    await self.mediator.workers.save_parallel_operation(conn, operation)

    async def run_callables(
        self,
        use_case: BaseParallelWorkerUseCase,
        operation: operations.BaseParallelOperation,
    ) -> None:
        """Run all nested commands."""
        futures = []
        try:
            callables = await use_case.execute(operation)  # type: ignore [attr-defined]
        except Exception:
            LOG.exception('Failed to get callables for {}', operation)
            raise
        else:
            for each_callable in callables:
                future = self.executor.submit(each_callable)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                exc = future.exception()
                if exc is not None:
                    raise exc
