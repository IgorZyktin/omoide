"""Worker that performs operations one by one."""

from omoide import custom_logging
from omoide import utils
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.database.interfaces.abs_worker_repo import AbsWorkerRepo
from omoide.domain import SerialOperation
from omoide.workers.common.base_worker import BaseWorker
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class SerialWorker(BaseWorker[Config]):
    """Worker that performs operations one by one."""

    def __init__(
        self,
        config: Config,
        database: AbsDatabase,
        repo: AbsWorkerRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__(config, database, repo)
        self.has_lock = False

    async def execute(self) -> bool:
        """Perform workload."""
        if not self.has_lock:
            async with self.database.transaction() as conn:
                lock = await self.repo.take_serial_lock(conn, self.config.name)

            if not lock:
                return False

            LOG.info('Worker {} took lock', self.config.name)
            self.has_lock = True

        async with self.database.transaction() as conn:
            operation = await self.repo.get_next_serial_operation(
                conn=conn,
                worker_name=self.config.name,
            )

        if not operation:
            return False

        async with self.database.transaction() as conn:
            locked = await self.repo.lock_serial_operation(
                conn=conn,
                operation=operation,
                worker_name=self.config.name,
            )

        if not locked:
            return False

        return await self.execute_operation(operation)

    async def execute_operation(self, operation: SerialOperation) -> bool:
        """Perform workload."""
        done_something = False
        LOG.info('Executing operation {}', operation)
        try:
            done_something = await operation.execute(
                database=self.database,
                worker_repo=self.repo,
                batch_size=self.config.batch_size,
            )
        except Exception as exc:
            error = utils.exc_to_str(exc)
            async with self.database.transaction() as conn:
                await self.repo.mark_serial_operation_failed(
                    conn, operation, error
                )
            LOG.exception(
                'Operation {operation} failed because of {error}',
                operation=operation,
                error=error,
            )
        else:
            async with self.database.transaction() as conn:
                await self.repo.mark_serial_operation_done(conn, operation)
            LOG.info(
                'Operation {operation} complete in {duration:0.3f} sec.',
                operation=operation,
                duration=operation.duration,
            )

        return done_something

    async def stop(self, worker_name: str) -> None:
        """Start worker."""
        async with self.database.transaction() as conn:
            lock = await self.repo.release_serial_lock(conn, worker_name)
            if lock:
                LOG.info('Worker {} released lock', worker_name)
        await super().stop(worker_name)
