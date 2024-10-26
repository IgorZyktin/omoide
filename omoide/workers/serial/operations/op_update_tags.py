"""Update tags for item."""

from uuid import UUID

from omoide import custom_logging
from omoide import models
from omoide import serial_operations as so
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial import operations as op
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


class UpdateTagsExecutor(
    op.SerialOperationExecutor[Config, WorkerMediator],
):
    """Update tags for item."""

    operation: so.UpdateTagsSO

    async def execute(self) -> None:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(
                conn=conn,
                uuid=self.operation.item_uuid,
            )
            affected_users: set[UUID] = {item.owner_uuid, *item.permissions}

        await self.update_tags(
            item=item,
            affected_users=affected_users,
        )

        async with self.mediator.database.transaction() as conn:
            for user_uuid in affected_users:
                await self.mediator.workers.create_serial_operation(
                    conn=conn,
                    operation=so.RebuildKnownTagsUserSO(
                        extras={'user_uuid': str(user_uuid)},
                    ),
                )

            public_users = await self.mediator.users.get_public_users(conn)
            if public_users & affected_users:
                await self.mediator.workers.create_serial_operation(
                    conn=conn,
                    operation=so.RebuildKnownTagsAnonSO(),
                )

    async def update_tags(
        self,
        item: models.Item,
        affected_users: set[UUID],
    ) -> None:
        """Change tags in children."""
        all_computed_tags: set[str] = set()

        async with self.mediator.database.transaction() as conn:
            if item.parent_uuid is not None:
                parent = await self.mediator.items.get_by_uuid(
                    conn=conn,
                    uuid=item.parent_uuid,
                )
                parent_tags = await self.mediator.tags.get_computed_tags(
                    conn=conn,
                    item=parent,
                )
                all_computed_tags.update(parent_tags)

            async def _recursively_apply(current_item: models.Item) -> None:
                """Apply to at least one item and maybe its children."""
                computed_tags = current_item.get_computed_tags(
                    all_computed_tags
                )
                all_computed_tags.update(computed_tags)
                await self.mediator.tags.save_computed_tags(
                    conn, item, computed_tags
                )

                affected_users.update({item.owner_uuid, *item.permissions})

                if self.operation.apply_to_children:
                    children = await self.mediator.items.get_children(
                        conn=conn,
                        item=current_item,
                    )

                    for child in children:
                        LOG.info(
                            'Tags change in {parent} affected {child}',
                            parent=current_item,
                            child=child,
                        )
                        await _recursively_apply(child)

            await _recursively_apply(item)
