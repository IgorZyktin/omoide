"""Plugin that checks that every item has metainfo."""

from omoide import custom_logging
from omoide.omoide_cli.audit.base_plugin import BasePlugin

LOG = custom_logging.get_logger(__name__)


class ItemsToMetainfo(BasePlugin):
    """Plugin that checks that every item has metainfo."""

    async def execute(self) -> None:
        """Perform actions."""
        async with self.database.transaction() as conn:
            items_without_metainfo = await self.database.get_items_without_metainfo(conn)

            for item in items_without_metainfo:
                if self.fix:
                    await self.database.create_metainfo(conn, item)
                    LOG.info(
                        'Item {id} {name!r} ({uuid}) has no metainfo --- FIXED',
                        id=item.id,
                        name=item.name,
                        uuid=item.uuid,
                    )
                else:
                    LOG.warning(
                        'Item {id} {name!r} ({uuid}) has no metainfo',
                        id=item.id,
                        name=item.name,
                        uuid=item.uuid,
                    )
