"""Plugin that displays items that have no images."""

from omoide import custom_logging
from omoide.omoide_cli.audit.base_plugin import BasePlugin

LOG = custom_logging.get_logger(__name__)


class ItemsWithoutImages(BasePlugin):
    """Plugin that displays items that have no images."""

    async def execute(self) -> None:
        """Perform actions."""
        async with self.database.transaction() as conn:
            items_without_images = await self.database.get_items_without_images(conn)

            for item in items_without_images:
                LOG.warning(
                    'Item {id} {name!r} ({uuid}) has no image',
                    id=item.id,
                    name=item.name,
                    uuid=item.uuid,
                )
