"""Worker that performs operations in parallel."""

from concurrent.futures import ProcessPoolExecutor

from omoide import custom_logging
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.parallel.cfg import ParallelWorkerConfig

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

        for operation in batch:
            # TODO - pass it to the executor
            print(operation)  # noqa: T201
            _ = operation

        return True
