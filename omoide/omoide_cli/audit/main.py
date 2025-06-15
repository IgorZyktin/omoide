"""Audit operations."""

import asyncio

import typer

from omoide import const
from omoide import custom_logging
from omoide.omoide_cli import common
from omoide.omoide_cli.audit.base_plugin import BasePlugin
from omoide.omoide_cli.audit.database import AuditDatabase
from omoide.omoide_cli.audit.plugins.itesm_to_metainfo import ItemsToMetainfo
from omoide.omoide_cli.audit.plugins.users_to_root_items import UsersToRootItems

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


def audit(db_url: str | None = None, *, fix: bool = False) -> None:
    """Perform audit.

    Checks all invariants.
    """
    db_url = common.extract_env(
        what='Database URL',
        variable=db_url,
        env_variable=const.ENV_DB_URL_ADMIN,
    )

    database = AuditDatabase(db_url)

    plugins: list[BasePlugin] = [
        UsersToRootItems(database, fix=fix),
        ItemsToMetainfo(database, fix=fix),
    ]

    asyncio.run(actually_perform_audit(database, plugins))


async def actually_perform_audit(database: AuditDatabase, plugins: list[BasePlugin]) -> None:
    """Actually do something."""
    LOG.info('Doing audit')
    await database.connect()

    for plugin in plugins:
        try:
            await plugin.execute()
        except Exception:
            LOG.exception('Failed to execute {}', type(plugin).__name__)

    await database.disconnect()
    LOG.info('Audit complete')


if __name__ == '__main__':
    app()
