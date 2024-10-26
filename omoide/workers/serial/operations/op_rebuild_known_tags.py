"""Rebuild known tags for users."""

import time

from omoide import custom_logging
from omoide import serial_operations as so
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import operations as op
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class RebuildKnownTagsAnonExecutor(
    op.SerialOperationExecutor[Config, WorkerMediator],
):
    """Rebuild known tags for anon."""

    operation: so.RebuildKnownTagsAnonSO

    def execute(self) -> None:
        """Perform workload."""
        with self.mediator.database.transaction() as conn:
            tags = self.mediator.tags.get_known_tags_anon(
                conn,
                batch_size=self.config.input_batch,
            )
            self.mediator.tags.drop_known_tags_anon(conn)
            self.mediator.tags.insert_known_tags_anon(
                conn, tags, batch_size=self.config.output_batch
            )


class RebuildKnownTagsRegisteredExecutor(
    op.SerialOperationExecutor[Config, WorkerMediator],
):
    """Rebuild known tags for specific user."""

    operation: so.RebuildKnownTagsUserSO

    def execute(self) -> None:
        """Perform workload."""
        with self.mediator.database.transaction() as conn:
            user = self.mediator.users.get_by_uuid(
                conn, self.operation.user_uuid
            )

            self.operation.goal = f'rebuild known tags for {user}'

            tags = self.mediator.tags.get_known_tags_user(
                conn,
                user,
                batch_size=self.config.input_batch,
            )
            self.mediator.tags.drop_known_tags_user(conn, user)
            self.mediator.tags.insert_known_tags_user(
                conn, user, tags, batch_size=self.config.output_batch
            )


class RebuildKnownTagsAllExecutor(
    op.SerialOperationExecutor[Config, WorkerMediator],
):
    """Rebuild known tags for all registered users."""

    operation: so.RebuildKnownTagsAllSO

    def execute(self) -> None:
        """Perform workload."""
        LOG.info(
            'Operation {}. Updating known tags for all users',
            self.operation.id,
        )

        with self.mediator.database.transaction() as conn:
            users = self.mediator.users.select(conn)

            for step, user in enumerate(users, start=1):
                if self.mediator.stopping:
                    break
                start = time.monotonic()
                tags = self.mediator.tags.get_known_tags_user(
                    conn,
                    user,
                    batch_size=self.config.input_batch,
                )
                self.mediator.tags.drop_known_tags_user(conn, user)
                self.mediator.tags.insert_known_tags_user(
                    conn, user, tags, batch_size=self.config.output_batch
                )
                LOG.info(
                    '\t{step}, {user} updated in {duration:0.2f} sec.',
                    step=step,
                    user=user,
                    duration=time.monotonic() - start,
                )
