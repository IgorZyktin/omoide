"""Rebuild known tags for users."""

import time

from omoide import custom_logging
from omoide import models
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import Config
from omoide.workers.serial.operations import SerialOperationImplementation

LOG = custom_logging.get_logger(__name__)


class RebuildKnownTagsAnonOperation(SerialOperationImplementation):
    """Rebuild known tags for anon."""

    async def execute(self) -> None:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            tags = await self.mediator.tags.calculate_known_tags_anon(conn)
            await self.mediator.tags.drop_known_tags_anon(conn)
            await self.mediator.tags.insert_known_tags_anon(
                conn, tags, batch_size=self.config.output_batch
            )


class RebuildKnownTagsUserOperation(SerialOperationImplementation):
    """Rebuild known tags for specific user."""

    def __init__(
        self,
        operation: models.SerialOperation,
        config: Config,
        mediator: WorkerMediator,
    ) -> None:
        """Initialize instance."""
        super().__init__(operation, config, mediator)
        self.user_id = int(operation.extras['user_id'])

    async def execute(self) -> None:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            user = await self.mediator.users.get_by_id(conn, self.user_id)
            tags = await self.mediator.tags.calculate_known_tags_user(conn, user)
            await self.mediator.tags.drop_known_tags_user(conn, user)
            await self.mediator.tags.insert_known_tags_user(
                conn, user, tags, batch_size=self.config.output_batch
            )


class RebuildKnownTagsAllOperation(SerialOperationImplementation):
    """Rebuild known tags for all registered users."""

    async def execute(self) -> None:
        """Perform workload."""
        LOG.info('{}. Updating known tags for all users', self.operation)

        async with self.mediator.database.transaction() as conn:
            users = await self.mediator.users.select(conn)

        for step, user in enumerate(users, start=1):
            async with self.mediator.database.transaction() as conn:
                start = time.monotonic()
                tags = await self.mediator.tags.calculate_known_tags_user(conn, user)
                await self.mediator.tags.drop_known_tags_user(conn, user)
                await self.mediator.tags.insert_known_tags_user(
                    conn, user, tags, batch_size=self.config.output_batch
                )
                LOG.info(
                    '\t{step}, {user} updated in {duration:0.2f} sec.',
                    step=step,
                    user=user,
                    duration=time.monotonic() - start,
                )
