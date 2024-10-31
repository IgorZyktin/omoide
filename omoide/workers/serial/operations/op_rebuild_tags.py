"""Update tags for item."""

from omoide import custom_logging
from omoide import models
from omoide import serial_operations as so
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import operations as op
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class RebuildTagsExecutor(op.SerialOperationExecutor[Config, WorkerMediator]):
    """Update tags for item."""

    operation: so.RebuildItemTagsSO

    async def execute(self) -> None:
        """Perform workload."""
        affected_users: set[int] = set()

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_id(conn, self.operation.item_id)
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)
            is_public = owner.is_public

            if self.operation.apply_to_owner:
                affected_users.add(item.owner_id)

            if self.operation.apply_to_permissions:
                affected_users.update(item.permissions)

        await self.rebuild_tags(item, affected_users)

        if affected_users:
            async with self.mediator.database.transaction() as conn:
                for user_id in affected_users:
                    await self.mediator.workers.create_serial_operation(
                        conn=conn,
                        operation=so.RebuildKnownTagsUserSO(
                            extras={'user_id': user_id},
                        ),
                    )

                if self.operation.apply_to_anon and is_public:
                    await self.mediator.workers.create_serial_operation(
                        conn=conn,
                        operation=so.RebuildKnownTagsAnonSO(),
                    )

    async def rebuild_tags(self, item: models.Item, affected_users: set[int]) -> None:
        """Change tags in children."""
        all_computed_tags: set[str] = set()

        async with self.mediator.database.transaction() as conn:
            if item.parent_id is not None:
                parent = await self.mediator.items.get_by_id(conn, item.parent_id)
                parent_tags = await self.mediator.tags.get_computed_tags(conn, parent)
                all_computed_tags.update(parent_tags)

            async def _recursively_apply(current_item: models.Item) -> None:
                """Apply to at least one item and maybe its children."""
                computed_tags = current_item.get_computed_tags(all_computed_tags)
                all_computed_tags.update(computed_tags)
                await self.mediator.tags.save_computed_tags(conn, item, computed_tags)

                affected_users.update({item.owner_id, *item.permissions})

                if self.operation.apply_to_children:
                    children = await self.mediator.items.get_children(conn, current_item)

                    for child in children:
                        LOG.info(
                            'Tags change in {parent} affected {child}',
                            parent=current_item,
                            child=child,
                        )
                        await _recursively_apply(child)

            await _recursively_apply(item)
