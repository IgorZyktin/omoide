"""Use cases for permissions-related operations."""

from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide import operations
from omoide import utils
from omoide.workers.serial.use_cases.base_use_case import BaseSerialWorkerUseCase

LOG = custom_logging.get_logger(__name__)


class RebuildPermissionsForItemUseCase(BaseSerialWorkerUseCase):
    """Use case for rebuilding permissions for an item."""

    async def execute(self, operation: operations.Operation) -> None:
        """Perform workload."""
        affected_users: set[int] = set()

        if operation.extras['apply_to_parents']:
            await self.do_apply_to_parents(operation, affected_users)

        if operation.extras['apply_to_children']:
            await self.do_apply_to_children(operation, affected_users)

        async with self.mediator.database.transaction() as conn:
            for user_id in affected_users:
                user = await self.mediator.users.get_by_id(conn, user_id)
                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    name='rebuild_known_tags_for_user',
                    extras={
                        'requested_by': operation.extras['requested_by'],
                        'user_uuid': str(user.uuid),
                        'only_tags': None,
                    },
                )

            public_users = await self.mediator.users.get_public_user_ids(conn)
            if public_users & affected_users:
                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    name='rebuild_known_tags_for_anon',
                    extras={
                        'requested_by': operation.extras['requested_by'],
                        'only_tags': None,
                    },
                )

    async def do_apply_to_parents(
        self,
        operation: operations.Operation,
        affected_users: set[int],
    ) -> None:
        """Change permissions in parents."""
        item_uuid = UUID(operation.extras['item_uuid'])
        added = set(operation.extras['added'])
        deleted = set(operation.extras['deleted'])

        affected_users.update(added)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            parents = await self.mediator.items.get_parents(conn, item)

            for parent in reversed(parents):
                if parent.status is models.Status.DELETED:
                    return

                parent.permissions = parent.permissions | added
                parent.permissions = parent.permissions - deleted
                await self.mediator.items.save(conn, parent)
                LOG.info(
                    'Permissions change in child {child} affected parent {parent}',
                    child=item,
                    parent=parent,
                )

    async def do_apply_to_children(
        self,
        operation: operations.Operation,
        affected_users: set[int],
    ) -> None:
        """Change permissions in children."""
        item_uuid = UUID(operation.extras['item_uuid'])
        added = set(operation.extras['added'])
        deleted = set(operation.extras['deleted'])
        original = set(operation.extras['original'])

        async with self.mediator.database.transaction() as conn:
            top_item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            top_children = await self.mediator.items.get_children(conn=conn, item=top_item)

            async def _recursively_apply(
                parent: models.Item,
                child: models.Item,
            ) -> None:
                """Call on all subsequent children."""
                if child.status is models.Status.DELETED:
                    return

                if operation.extras['apply_to_children_as'] == const.ApplyAs.COPY:
                    sub_added, sub_deleted = utils.get_delta(
                        before=child.permissions,
                        after=original,
                    )
                    child.permissions = original
                    affected_users.update(sub_added | sub_deleted)

                elif operation.extras['apply_to_children_as'] == const.ApplyAs.DELTA:
                    child.permissions = child.permissions | added
                    child.permissions = child.permissions - deleted
                    affected_users.update(added | deleted)

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
