"""Rebuild known tags for users."""

from dataclasses import dataclass
import time
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


@dataclass
class DummyOperation(models.SerialOperation[Config, WorkerMediator]):
    """Operation for testing purposes."""

    name: str = const.SERIAL_DUMMY

    def execute(self, config: Config, mediator: WorkerMediator) -> None:
        """Perform workload."""


@dataclass
class RebuildKnownTagsAnonSerialOperation(
    models.SerialOperation[Config, WorkerMediator],
):
    """Rebuild known tags for anon."""

    name: str = const.SERIAL_REBUILD_KNOWN_TAGS_ANON
    goal: str = 'rebuild known tags for anon'

    def execute(self, config: Config, mediator: WorkerMediator) -> None:
        """Perform workload."""
        with mediator.database.transaction() as conn:
            tags = mediator.tags.get_known_tags_anon(
                conn,
                batch_size=config.input_batch,
            )
            mediator.tags.drop_known_tags_anon(conn)
            mediator.tags.insert_known_tags_anon(
                conn, tags, batch_size=config.output_batch
            )


@dataclass
class RebuildKnownTagsUserSerialOperation(
    models.SerialOperation[Config, WorkerMediator],
):
    """Rebuild known tags for specific user."""

    name: str = const.SERIAL_REBUILD_KNOWN_TAGS_USER

    def execute(self, config: Config, mediator: WorkerMediator) -> None:
        """Perform workload."""
        user_id: int | None = self.extras.get('user_id')
        user_uuid: str | None = self.extras.get('user_uuid')

        msg = f'There is no user with id={user_id!r} or uuid={user_uuid!r}'
        if user_id is None and user_uuid is None:
            raise exceptions.DoesNotExistError(msg)

        with mediator.database.transaction() as conn:
            if user_id is None:
                user = mediator.users.get_by_uuid(conn, UUID(user_uuid))
            elif user_uuid is None:
                user = mediator.users.get_by_id(conn, user_id)
            else:
                raise exceptions.DoesNotExistError(msg)

            self.goal = f'rebuild known tags for {user}'

            tags = mediator.tags.get_known_tags_user(
                conn,
                user,
                batch_size=config.input_batch,
            )
            mediator.tags.drop_known_tags_user(conn, user)
            mediator.tags.insert_known_tags_user(
                conn, user, tags, batch_size=config.output_batch
            )


@dataclass
class RebuildKnownTagsAllSerialOperation(
    models.SerialOperation[Config, WorkerMediator],
):
    """Rebuild known tags for all registered users."""

    name: str = const.SERIAL_REBUILD_KNOWN_TAGS_ALL
    goal: str = 'rebuild known tags for all users'

    def execute(self, config: Config, mediator: WorkerMediator) -> None:
        """Perform workload."""
        LOG.info('Operation {}. Updating known tags for all users', self.id)

        with mediator.database.transaction() as conn:
            users = mediator.users.select(conn)

            for step, user in enumerate(users, start=1):
                if mediator.stopping:
                    break
                start = time.monotonic()
                tags = mediator.tags.get_known_tags_user(
                    conn,
                    user,
                    batch_size=config.input_batch,
                )
                mediator.tags.drop_known_tags_user(conn, user)
                mediator.tags.insert_known_tags_user(
                    conn, user, tags, batch_size=config.output_batch
                )
                LOG.info(
                    '\t{step}, {user} updated in {duration:0.2f} sec.',
                    step=step,
                    user=user,
                    duration=time.monotonic() - start,
                )
