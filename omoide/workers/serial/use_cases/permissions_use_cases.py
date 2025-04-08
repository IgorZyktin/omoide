"""Use cases for permissions-related operations."""

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide import utils
from omoide.workers.serial.use_cases.base_use_case import BaseSerialWorkerUseCase

LOG = custom_logging.get_logger(__name__)


class RebuildPermissionsForItemUseCase(BaseSerialWorkerUseCase):
    """Use case for rebuilding permissions for an item."""

    async def execute(self, request: models.RebuildPermissionsForItemRequest) -> None:
        """Perform workload."""
        affected_users: set[int] = set()

        if request.apply_to_parents:
            await self.do_apply_to_parents(request, affected_users)

        if request.apply_to_children:
            await self.do_apply_to_children(request, affected_users)

        async with self.mediator.database.transaction() as conn:
            for user_id in affected_users:
                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    request=models.RebuildKnownTagsForUserRequest(
                        requested_by_user_id=request.requested_by_user_id,
                        user_id=user_id,
                    ),
                )

            public_users = await self.mediator.users.get_public_user_ids(conn)
            if public_users & affected_users:
                await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    request=models.RebuildKnownTagsForAnonRequest(
                        requested_by_user_id=request.requested_by_user_id,
                    ),
                )

    async def do_apply_to_parents(
        self,
        request: models.RebuildPermissionsForItemRequest,
        affected_users: set[int],
    ) -> None:
        """Change permissions in parents."""
        affected_users.update(request.added)

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_id(conn, request.item_id)
            parents = await self.mediator.items.get_parents(conn, item)

            for parent in reversed(parents):
                if parent.status is models.Status.DELETED:
                    return

                parent.permissions = parent.permissions | set(request.added)
                parent.permissions = parent.permissions - set(request.deleted)
                await self.mediator.items.save(conn, parent)
                LOG.info(
                    'Permissions change in child {child} affected parent {parent}',
                    child=item,
                    parent=parent,
                )

    async def do_apply_to_children(
        self,
        request: models.RebuildPermissionsForItemRequest,
        affected_users: set[int],
    ) -> None:
        """Change permissions in children."""
        async with self.mediator.database.transaction() as conn:
            top_item = await self.mediator.items.get_by_id(conn, request.item_id)
            top_children = await self.mediator.items.get_children(conn=conn, item=top_item)

            async def _recursively_apply(
                parent: models.Item,
                child: models.Item,
            ) -> None:
                """Call on all subsequent children."""
                if child.status is models.Status.DELETED:
                    return

                if request.apply_to_children_as == const.ApplyAs.COPY:
                    sub_added, sub_deleted = utils.get_delta(
                        before=child.permissions,
                        after=request.original,
                    )
                    child.permissions = set(request.original)
                    affected_users.update(sub_added | sub_deleted)

                elif request.apply_to_children_as == const.ApplyAs.DELTA:
                    added = set(request.added)
                    deleted = set(request.deleted)
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
