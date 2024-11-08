"""Update tags for item."""

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import Config
from omoide.workers.serial.operations import SerialOperationImplementation

LOG = custom_logging.get_logger(__name__)


class RebuildItemTagsOperation(SerialOperationImplementation):
    """Update tags for item."""

    def __init__(
        self,
        operation: models.SerialOperation,
        config: Config,
        mediator: WorkerMediator,
    ) -> None:
        """Initialize instance."""
        super().__init__(operation, config, mediator)
        self.item_id = int(operation.extras['item_id'])
        self.apply_to_children = bool(operation.extras['apply_to_children'])
        self.apply_to_owner = bool(operation.extras['apply_to_owner'])
        self.apply_to_permissions = bool(operation.extras['apply_to_permissions'])
        self.apply_to_anon = bool(operation.extras['apply_to_anon'])

    async def execute(self) -> None:
        """Perform workload."""
        affected_users: set[int] = set()

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_id(conn, self.item_id)
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)
            is_public = owner.is_public

            if self.apply_to_owner:
                affected_users.add(item.owner_id)

            if self.apply_to_permissions:
                affected_users.update(item.permissions)

        await self.rebuild_tags(item, affected_users)

        if affected_users:
            async with self.mediator.database.transaction() as conn:
                for user_id in affected_users:
                    await self.mediator.misc.create_serial_operation(
                        conn=conn,
                        name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_USER,
                        extras={'user_id': user_id},
                    )

                if self.apply_to_anon and is_public:
                    await self.mediator.misc.create_serial_operation(
                        conn=conn,
                        name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_ANON,
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
                await self.mediator.tags.save_computed_tags(conn, current_item, computed_tags)

                affected_users.update({current_item.owner_id, *current_item.permissions})

                if self.apply_to_children:
                    children = await self.mediator.items.get_children(conn, current_item)

                    for child in children:
                        if child.status is models.Status.DELETED:
                            continue

                        LOG.info(
                            'Tags change in parent {parent} affected child {child}',
                            parent=current_item,
                            child=child,
                        )
                        await _recursively_apply(child)

            await _recursively_apply(item)
