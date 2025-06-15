"""Plugin that checks that every user has exactly one root item."""

from collections import defaultdict

from omoide import custom_logging
from omoide.omoide_cli.audit.base_plugin import BasePlugin

LOG = custom_logging.get_logger(__name__)


class UsersToRootItems(BasePlugin):
    """Plugin that checks that every user has exactly one root item."""

    async def execute(self) -> None:
        """Perform actions."""
        async with self.database.transaction() as conn:
            users_to_root_items = await self.database.get_users_to_root_items(conn)

            mapping = defaultdict(list)

            for user, item in users_to_root_items:
                mapping[user].append(item)

            for user, items in mapping.items():
                match len(items):
                    case 0:
                        if self.fix:
                            await self.database.fix_root_item(conn, user)
                            LOG.info(
                                'User {id} {name!r} ({uuid}) has no root items --- FIXED',
                                id=user.id,
                                name=user.name,
                                uuid=user.uuid,
                            )
                        else:
                            LOG.warning(
                                'User {id} {name!r} ({uuid}) has no root items',
                                id=user.id,
                                name=user.name,
                                uuid=user.uuid,
                            )
                    case 1:
                        # everything is okay
                        pass
                    case _:
                        readable_items = '\n'.join(
                            [
                                f'<id={item.id}, name={item.name!r}, uuid={item.uuid}>'
                                for item in items
                            ]
                        )
                        LOG.error(
                            'User {id} {name!r} ({uuid}) has more '
                            'than one root item (cannot be fixed automatically)\n'
                            '{readable_items}',
                            id=user.id,
                            name=user.name,
                            uuid=user.uuid,
                            readable_items=readable_items,
                        )
