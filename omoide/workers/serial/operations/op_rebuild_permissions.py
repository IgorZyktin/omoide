"""Update permissions for item."""

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide import utils
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import Config
from omoide.workers.serial.operations import SerialOperationImplementation

LOG = custom_logging.get_logger(__name__)


class RebuildItemPermissionsOperation(SerialOperationImplementation):
    """Update permission for item."""

    def __init__(
        self,
        operation: models.SerialOperation,
        config: Config,
        mediator: WorkerMediator,
    ) -> None:
        """Initialize instance."""
        super().__init__(operation, config, mediator)
        self.item_id = int(operation.extras['item_id'])
        self.added: set[int] = set(operation.extras['added'])
        self.deleted: set[int] = set(operation.extras['deleted'])
        self.original: set[int] = set(operation.extras['original'])
        self.apply_to_parents = bool(operation.extras['apply_to_parents'])
        self.apply_to_children = bool(operation.extras['apply_to_children'])
        self.apply_to_children_as = const.ApplyAs(operation.extras['apply_to_children_as'])

    async def execute(self) -> None:
        """Perform workload."""
        affected_users: set[int] = set()

        if self.apply_to_parents:
            await self.do_apply_to_parents(affected_users)

        if self.apply_to_children:
            await self.do_apply_to_children(affected_users)

        async with self.mediator.database.transaction() as conn:
            for user_id in affected_users:
                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_USER,
                    extras={'user_id': user_id},
                )

            public_users = await self.mediator.users.get_public_user_ids(conn)
            if public_users & affected_users:
                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_ANON,
                )

    async def do_apply_to_parents(self, affected_users: set[int]) -> None:
        """Change permissions in parents."""
        affected_users.update(self.added)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_id(conn, self.item_id)
            parents = await self.mediator.items.get_parents(conn, item)

            for parent in reversed(parents):
                if parent.status is models.Status.DELETED:
                    return

                parent.permissions = parent.permissions | self.added
                parent.permissions = parent.permissions - self.deleted
                await self.mediator.items.save(conn, parent)
                LOG.info(
                    'Permissions change in child {child} affected parent {parent}',
                    child=item,
                    parent=parent,
                )

    async def do_apply_to_children(self, affected_users: set[int]) -> None:
        """Change permissions in children."""
        async with self.mediator.database.transaction() as conn:
            top_item = await self.mediator.items.get_by_id(conn, self.item_id)
            top_children = await self.mediator.items.get_children(conn=conn, item=top_item)

            async def _recursively_apply(
                parent: models.Item,
                child: models.Item,
            ) -> None:
                """Call on all subsequent children."""
                if child.status is models.Status.DELETED:
                    return

                if self.apply_to_children_as is const.ApplyAs.COPY:
                    sub_added, sub_deleted = utils.get_delta(
                        before=child.permissions,
                        after=self.original,
                    )
                    child.permissions = self.original
                    affected_users.update(sub_added | sub_deleted)

                elif self.apply_to_children_as is const.ApplyAs.DELTA:
                    child.permissions = child.permissions | self.added
                    child.permissions = child.permissions - self.deleted
                    affected_users.update(self.added | self.deleted)

                await self.mediator.items.save(conn, child)
                LOG.info(
                    'Permissions change in parent {parent} affected child {child}',
                    parent=parent,
                    child=child,
                )

                sub_children = await self.mediator.items.get_children(conn=conn, item=child)

                for sub_child in sub_children:
                    await _recursively_apply(child, sub_child)

            for top_child in top_children:
                await _recursively_apply(top_item, top_child)
