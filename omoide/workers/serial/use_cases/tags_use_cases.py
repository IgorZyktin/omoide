"""Use cases for tags-related operations."""

from typing import Any
from uuid import UUID

from omoide import custom_logging
from omoide import models
from omoide import operations
from omoide.workers.serial.cfg import SerialWorkerConfig
from omoide.workers.serial.mediator import SerialWorkerMediator
from omoide.workers.serial.use_cases.base_use_case import BaseSerialWorkerUseCase

LOG = custom_logging.get_logger(__name__)


class RebuildKnownTagsForAnonUseCase(BaseSerialWorkerUseCase):
    """Use case for rebuilding known tags for anon."""

    async def execute(self, operation: operations.Operation) -> None:
        """Perform workload."""
        only_tags = operation.extras['only_tags']

        async with self.mediator.database.transaction() as conn:
            tags = await self.mediator.tags.calculate_known_tags_anon(conn, only_tags)
            LOG.debug('Got {} tags for anon', len(tags))
            dropped = await self.mediator.tags.drop_known_tags_anon(conn, only_tags)
            LOG.debug('Dropped {} tags', dropped)
            await self.mediator.tags.insert_known_tags_anon(
                conn, tags, batch_size=self.config.output_batch
            )


class RebuildKnownTagsForUserUseCase(BaseSerialWorkerUseCase):
    """Use case for rebuilding known tags for known user."""

    async def execute(self, operation: operations.Operation) -> None:
        """Perform workload."""
        user_uuid = UUID(operation.extras['user_uuid'])
        only_tags = operation.extras['only_tags']

        async with self.mediator.database.transaction() as conn:
            user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            tags = await self.mediator.tags.calculate_known_tags_user(conn, user, only_tags)
            LOG.debug('Got {} tags for {}', len(tags), user)
            dropped = await self.mediator.tags.drop_known_tags_user(conn, user, only_tags)
            LOG.debug('Dropped {} tags', dropped)
            await self.mediator.tags.insert_known_tags_user(
                conn, user, tags, batch_size=self.config.output_batch
            )


class RebuildKnownTagsForAllUseCase(BaseSerialWorkerUseCase):
    """Use case for rebuilding known tags for all users."""

    async def execute(self, operation: operations.Operation) -> None:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            users = await self.mediator.users.select(conn)

            for user in users:
                operation_id = await self.mediator.misc.create_serial_operation(
                    conn=conn,
                    name='rebuild_known_tags_for_user',
                    extras={
                        'requested_by': operation.extras['requested_by'],
                        'user_uuid': str(user.uuid),
                        'only_tags': None,
                    },
                )
                LOG.debug(
                    'Created serial operation {} (rebuilding known tags for user {})',
                    operation_id,
                    user,
                )

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name='rebuild_known_tags_for_anon',
                extras={
                    'requested_by': operation.extras['requested_by'],
                    'only_tags': None,
                },
            )
            LOG.debug('Created serial operation {} (rebuilding known tags for anon)', operation_id)


class RebuildComputedTagsForItemUseCase(BaseSerialWorkerUseCase):
    """Update tags for item."""

    def __init__(self, config: SerialWorkerConfig, mediator: SerialWorkerMediator) -> None:
        """Initialize instance."""
        super().__init__(config, mediator)
        self._items_cache: dict[UUID, models.Item] = {}
        self._computed_tags_cache: dict[int, set[str]] = {}

    async def _get_cached_item(self, conn: Any, item_uuid: UUID) -> models.Item:
        """Perform cached request."""
        item = self._items_cache.get(item_uuid)

        if item is not None:
            return item

        item = await self.mediator.items.get_by_uuid(conn, item_uuid)
        self._items_cache[item.uuid] = item
        return item

    async def _get_cached_computed_tags(self, conn: Any, item: models.Item) -> set[str]:
        """Perform cached request."""
        tags = self._computed_tags_cache.get(item.id)

        if tags is not None:
            return tags

        tags = await self.mediator.tags.get_computed_tags(conn, item)
        self._computed_tags_cache[item.id] = tags
        return tags

    async def execute(self, operation: operations.Operation) -> None:
        """Perform workload."""
        affected_users: set[int] = set()

        async with self.mediator.database.transaction() as conn:
            item_uuid = UUID(operation.extras['item_uuid'])
            item = await self._get_cached_item(conn, item_uuid)
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)
            is_public = owner.is_public

            # also update known tags for all who can see this
            affected_users.add(item.owner_id)
            affected_users.update(item.permissions)

        affected_tags = await self.rebuild_tags(item, affected_users)

        if affected_users:
            for user_id in affected_users:
                async with self.mediator.database.transaction() as conn:
                    user = await self.mediator.users.get_by_id(conn, user_id)
                    operation_id = await self.mediator.misc.create_serial_operation(
                        conn=conn,
                        name='rebuild_known_tags_for_user',
                        extras={
                            'requested_by': operation.extras['requested_by'],
                            'user_uuid': str(user.uuid),
                            'only_tags': list(affected_tags),
                        },
                    )
                    LOG.debug(
                        'Created serial operation {} (rebuilding known tags for user {})',
                        operation_id,
                        user_id,
                    )

            async with self.mediator.database.transaction() as conn:
                if is_public:
                    operation_id = await self.mediator.misc.create_serial_operation(
                        conn=conn,
                        name='rebuild_known_tags_for_anon',
                        extras={
                            'requested_by': operation.extras['requested_by'],
                            'only_tags': list(affected_tags),
                        },
                    )
                    LOG.debug(
                        'Created serial operation {} (rebuilding known tags for anon)',
                        operation_id,
                    )

    async def rebuild_tags(self, item: models.Item, affected_users: set[int]) -> set[str]:
        """Change tags in children."""
        affected_tags: set[str] = set()

        async with self.mediator.database.transaction() as conn:

            async def _recursively_apply(current_item: models.Item) -> None:
                """Apply to at least one item and maybe its children."""
                parent_tags: set[str] = set()

                parent_name = ''
                if current_item.parent_uuid is not None:
                    parent = await self._get_cached_item(conn, current_item.parent_uuid)
                    parent_tags = await self._get_cached_computed_tags(conn, parent)
                    parent_name = parent.name

                computed_tags = current_item.get_computed_tags(parent_name, parent_tags)
                affected_tags.update(computed_tags)
                # NOTE: outputting private tags could be a security risk
                LOG.debug('{} got computed tags {}', current_item, sorted(computed_tags))
                await self.mediator.tags.save_computed_tags(conn, current_item, computed_tags)

                affected_users.update({current_item.owner_id, *current_item.permissions})
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

        return affected_tags
