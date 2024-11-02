"""Worker that performs operations in parallel."""

from concurrent.futures import ProcessPoolExecutor

from omoide import custom_logging
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class ParallelWorker(BaseWorker[Config]):
    """Worker that performs operations in parallel."""

    def __init__(
        self,
        config: Config,
        mediator: WorkerMediator,
        executor: ProcessPoolExecutor,
    ) -> None:
        """Initialize instance."""
        super().__init__(config, mediator)
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
            _ = operation

        return True
