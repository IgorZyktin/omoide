"""Update tags for item."""

from typing import Any

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
        self._users_cache: dict[int, models.User] = {}
        self._items_cache: dict[int, models.Item] = {}
        self._computed_tags_cache: dict[int, set[str]] = {}

    async def _get_cached_user(self, conn: Any, user_id: int) -> models.User:
        """Perform cached request."""
        user = self._users_cache.get(user_id)

        if user is not None:
            return user

        user = await self.mediator.users.get_by_id(conn, user_id)
        self._users_cache[user.id] = user
        return user

    async def _get_cached_item(self, conn: Any, item_id: int) -> models.Item:
        """Perform cached request."""
        item = self._items_cache.get(item_id)

        if item is not None:
            return item

        item = await self.mediator.items.get_by_id(conn, item_id)
        self._items_cache[item.id] = item
        return item

    async def _get_cached_computed_tags(self, conn: Any, item: models.Item) -> set[str]:
        """Perform cached request."""
        tags = self._computed_tags_cache.get(item.id)

        if tags is not None:
            return tags

        tags = await self.mediator.tags.get_computed_tags(conn, item)
        self._computed_tags_cache[item.id] = tags
        return tags

    async def execute(self) -> None:
        """Perform workload."""
        affected_users: set[int] = set()

        async with self.mediator.database.transaction() as conn:
            item = await self._get_cached_item(conn, self.item_id)
            owner = await self._get_cached_user(conn, item.owner_id)
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
        async with self.mediator.database.transaction() as conn:

            async def _recursively_apply(current_item: models.Item) -> None:
                """Apply to at least one item and maybe its children."""
                parent_tags: set[str] = set()

                if current_item.parent_id is not None:
                    parent = await self._get_cached_item(conn, current_item.parent_id)
                    parent_tags = await self._get_cached_computed_tags(conn, parent)

                computed_tags = current_item.get_computed_tags(parent_tags)
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
