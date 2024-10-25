"""Update permissions for item."""

from dataclasses import dataclass
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import Config

LOG = custom_logging.get_logger(__name__)


@dataclass
class UpdatePermissions(models.SerialOperation[Config, WorkerMediator]):
    """Update permission for item."""

    name: str = const.SERIAL_UPDATE_PERMISSIONS
    goal: str = 'update permissions for item'

    def execute(self, config: Config, mediator: WorkerMediator) -> None:
        """Perform workload."""
        if self.extras['apply_to_parents']:
            self._apply_to_parents(mediator)

        if self.extras['apply_to_children']:
            self._apply_to_children(mediator)

    def _apply_to_parents(self, mediator: WorkerMediator) -> None:
        """Change permissions in parents."""
        item_uuid = UUID(self.extras['item_uuid'])
        added = {UUID(x) for x in self.extras['added']}

        with mediator.database.transaction() as conn:
            target_item = mediator.items.get_by_uuid(conn, item_uuid)
            parents = mediator.items.get_parents(conn, target_item)

            LOG.info('Updating permissions in parents of {}', target_item)
            for parent in reversed(parents):
                parent.permissions = parent.permissions | added
                mediator.items.save(conn, parent)
                LOG.info('\tUpdated permissions of {}', parent)

    def _apply_to_children(self, mediator: WorkerMediator) -> None:
        """Change permissions in children."""
        item_uuid = UUID(self.extras['item_uuid'])
        added = {UUID(x) for x in self.extras['added']}
        deleted = {UUID(x) for x in self.extras['deleted']}
        original = {UUID(x) for x in self.extras['original']}
        apply_to_children_as = const.ApplyAs(
            self.extras['apply_to_children_as']
        )

        with mediator.database.transaction() as conn:
            target_item = mediator.items.get_by_uuid(conn, item_uuid)
            children = mediator.items.get_children(conn, target_item)
            LOG.info('Updating permissions in children of {}', target_item)

            def _recursively_apply(item: models.Item) -> None:
                """Call on all subsequent children."""
                if apply_to_children_as is const.ApplyAs.COPY:
                    item.permissions = original

                elif apply_to_children_as is const.ApplyAs.DELTA:
                    item.permissions = item.permissions | added
                    item.permissions = item.permissions - deleted

                mediator.items.save(conn, item)
                LOG.info('\tUpdated permissions of {}', item)

                sub_children = mediator.items.get_children(conn, item)
                for sub_child in sub_children:
                    _recursively_apply(sub_child)

            for child in children:
                _recursively_apply(child)
