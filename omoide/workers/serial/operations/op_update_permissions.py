"""Update permissions for item."""

from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide import serial_operations as so
from omoide import utils
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import operations as op
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class UpdatePermissionsExecutor(
    op.SerialOperationExecutor[Config, WorkerMediator],
):
    """Update permission for item."""

    operation: so.UpdatePermissionsSO

    async def execute(self) -> None:
        """Perform workload."""
        affected_users: set[UUID] = set()

        if self.operation.apply_to_parents:
            await self.apply_to_parents(affected_users)

        if self.operation.apply_to_children:
            await self.apply_to_children(affected_users)

        async with self.mediator.database.transaction() as conn:
            for user_uuid in affected_users:
                await self.mediator.workers.create_serial_operation(
                    conn=conn,
                    operation=so.RebuildKnownTagsUserSO(
                        extras={'user_uuid': str(user_uuid)},
                    ),
                )

            public_users = await self.mediator.users.get_public_user_uuids(conn)
            if public_users & affected_users:
                await self.mediator.workers.create_serial_operation(
                    conn=conn,
                    operation=so.RebuildKnownTagsAnonSO(),
                )

    async def apply_to_parents(self, affected_users: set[UUID]) -> None:
        """Change permissions in parents."""
        affected_users.update(self.operation.added)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(
                conn=conn,
                uuid=self.operation.item_uuid,
            )

            parents = await self.mediator.items.get_parents(conn, item)

            for parent in reversed(parents):
                parent.permissions = parent.permissions | self.operation.added
                parent.permissions = parent.permissions - self.operation.deleted
                await self.mediator.items.save(conn, parent)
                LOG.info(
                    'Permissions change in {child} affected {parent} (parent)',
                    child=item,
                    parent=parent,
                )

    async def apply_to_children(self, affected_users: set[UUID]) -> None:
        """Change permissions in children."""
        async with self.mediator.database.transaction() as conn:
            top_item = await self.mediator.items.get_by_uuid(
                conn=conn,
                uuid=self.operation.item_uuid,
            )

            top_children = await self.mediator.items.get_children(
                conn=conn,
                item=top_item,
            )

            async def _recursively_apply(
                parent: models.Item,
                child: models.Item,
            ) -> None:
                """Call on all subsequent children."""
                if self.operation.apply_to_children_as is const.ApplyAs.COPY:
                    sub_added, sub_deleted = utils.get_delta(
                        before=child.permissions,
                        after=self.operation.original,
                    )
                    child.permissions = self.operation.original
                    affected_users.update(sub_added | sub_deleted)

                elif self.operation.apply_to_children_as is const.ApplyAs.DELTA:
                    child.permissions = child.permissions | self.operation.added
                    child.permissions = child.permissions - self.operation.deleted
                    affected_users.update(self.operation.added | self.operation.deleted)

                await self.mediator.items.save(conn, child)
                LOG.info(
                    'Permissions change in {parent} affected {child} (child)',
                    parent=parent,
                    child=child,
                )

                sub_children = await self.mediator.items.get_children(
                    conn=conn,
                    item=child,
                )

                for sub_child in sub_children:
                    await _recursively_apply(child, sub_child)

            for top_child in top_children:
                await _recursively_apply(top_item, top_child)
