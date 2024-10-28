"""Manual CLI operations."""


import click
from pydantic import SecretStr

from omoide import custom_logging
from omoide import utils
from omoide.commands import helpers
from omoide.storage.database import sync_db

LOG = custom_logging.get_logger(__name__)


@click.group()
def cli() -> None:
    """Manual CLI operations."""


@cli.command(name='refresh_file_sizes_in_db')
@click.option(
    '--db-url',
    required=True,
    help='Database URL',
)
@click.option(
    '--hot-folder',
    default='',
    help='Location of the hot folder (optional)',
    show_default=True,
)
@click.option(
    '--cold-folder',
    default='',
    help='Location of the cold folder (optional)',
    show_default=True,
)
@click.option(
    '--only-users',
    help='Apply to one or more specially listed users (comma separated)',
)
@click.option(
    '--log-every-item/--no-log-every-item',
    default=False,
    help='Output every refreshed item',
)
@click.option(
    '--limit',
    type=int,
    default=-1,
    help='Maximum amount of items to process (-1 for infinity)',
)
@click.option(
    '--marker',
    default='',
    help='Item from which we should start',
)
def command_refresh_file_sizes_in_db(**kwargs: str | int | bool) -> None:
    """Recalculate all file sizes for every item."""
    from omoide.commands.refresh_file_sizes_in_db import cfg
    from omoide.commands.refresh_file_sizes_in_db import run

    db_url = SecretStr(str(kwargs.pop('db_url')))

    only_users = []
    if kwargs.pop('only_users', ''):
        only_users = utils.split(str(kwargs.pop('only_users', '')))

    config = cfg.Config(db_url=db_url, only_users=only_users, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with (
        database.life_cycle(),
        helpers.timing(
            callback=LOG.info,
            start_template='Refreshing file sizes for every item...',
        ),
    ):
        run.run(config, database)


@cli.command(name='rebuild_image_sizes')
@click.option(
    '--db-url',
    required=True,
    help='Database URL',
)
@click.option(
    '--hot-folder',
    default='',
    help='Location of the hot folder (optional)',
    show_default=True,
)
@click.option(
    '--cold-folder',
    default='',
    help='Location of the cold folder (optional)',
    show_default=True,
)
@click.option(
    '--only-users',
    help='Apply to one or more specially listed users (comma separated)',
)
@click.option(
    '--only-corrupted',
    default=True,
    help='Do not override metainfo that is already fine',
)
@click.option(
    '--log-every-item/--no-log-every-item',
    default=False,
    help='Output every refreshed item',
)
@click.option(
    '--limit',
    type=int,
    default=-1,
    help='Maximum amount of items to process (-1 for infinity)',
)
def command_rebuild_image_sizes(**kwargs: int | str | bool) -> None:
    """Rebuild all content/preview/thumbnail sizes."""
    from omoide.commands.rebuild_image_sizes import cfg
    from omoide.commands.rebuild_image_sizes import run

    db_url = SecretStr(str(kwargs.pop('db_url')))

    only_users = []
    if kwargs.pop('only_users', ''):
        only_users = utils.split(str(kwargs.pop('only_users', '')))

    config = cfg.Config(db_url=db_url, only_users=only_users, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(callback=LOG.info, start_template='Rebuilding all image sizes...'):
            run.run(config, database)


if __name__ == '__main__':
    cli()
