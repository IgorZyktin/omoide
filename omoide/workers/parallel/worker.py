"""Worker that performs operations in parallel."""

import concurrent
from concurrent.futures import ProcessPoolExecutor

from omoide import custom_logging
from omoide import exceptions
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
        executor: ProcessPoolExecutor,
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

        futures = []
        for operation in batch:
            use_case = self.get_use_case(operation.name)
            future = self.executor.submit(use_case.execute, request=operation)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            exc = future.exception()

            if exc is not None:
                LOG.exception(str(exc))

        return bool(futures)

    def get_use_case(self, operation_name: str) -> BaseParallelWorkerUseCase:
        """Return use case."""
        pair = NAMES_TO_USE_CASES.get(operation_name)

        if pair is None:
            raise exceptions.UnknownParallelOperationError(name=operation_name)

        use_case_type = pair['use_case_type']
        use_case = use_case_type(self.config)
        return use_case
