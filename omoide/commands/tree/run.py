"""Output all descendants of given item."""

from omoide import custom_logging
from omoide import utils
from omoide.commands import helpers
from omoide.commands.tree.cfg import Config
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(config: Config, database: SyncDatabase) -> None:
    """Output all descendants of given item."""
    LOG.info('\nConfig:\n{}', utils.serialize_model(config))

    print()
    with database.start_session() as session:
        item = helpers.get_item(session, item_uuid=config.item_uuid)
        helpers.output_tree(session, item, show_uuids=config.show_uuids)
    print()
