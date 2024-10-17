"""Manual CLI operations."""

from uuid import UUID

import click
from pydantic import SecretStr

from omoide import custom_logging
from omoide import utils
from omoide.commands import helpers
from omoide.storage.database import sync_db

LOG = custom_logging.get_logger(__name__)


@click.group()
def cli():
    """Manual CLI operations."""


@cli.command(name='du')
@click.option(
    '--db-url',
    required=True,
    help='Database URL',
)
@click.option(
    '--only-users',
    help='Apply to one or more specially listed users (comma separated)',
)
def command_du(**kwargs) -> None:
    """Show disk usage for every user."""
    from omoide.commands.du import cfg
    from omoide.commands.du import run

    db_url = SecretStr(kwargs.pop('db_url'))

    only_users = []
    if kwargs.pop('only_users', ''):
        only_users = utils.split(str(kwargs.pop('only_users', '')))

    config = cfg.Config(db_url=db_url, only_users=only_users)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with (
        database.life_cycle(),
        helpers.timing(
            callback=LOG.info,
            start_template='Calculating total disk usage...',
        ),
    ):
        run.run(config, database)


@cli.command(name='force_thumbnail_copying')
@click.option(
    '--db-url',
    required=True,
    help='Database URL',
)
@click.option(
    '--only-users',
    help='Apply to one or more specially listed users (comma separated)',
)
def command_force_cover_copying(**kwargs) -> None:
    """Force collections to explicitly write origins of their thumbnails.

    May require you to run it more than one time.
    """
    from omoide.commands.force_thumbnail_copying import cfg
    from omoide.commands.force_thumbnail_copying import run

    db_url = SecretStr(kwargs.pop('db_url'))

    only_users = []
    if kwargs.pop('only_users', ''):
        only_users = utils.split(str(kwargs.pop('only_users', '')))

    config = cfg.Config(db_url=db_url, only_users=only_users)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with (
        database.life_cycle(),
        helpers.timing(
            callback=LOG.info,
            start_template='Forcing items to copy thumbnails...',
        )
    ):
        run.run(config, database)


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
def command_refresh_file_sizes_in_db(**kwargs) -> None:
    """Recalculate all file sizes for every item."""
    from omoide.commands.refresh_file_sizes_in_db import cfg
    from omoide.commands.refresh_file_sizes_in_db import run

    db_url = SecretStr(kwargs.pop('db_url'))

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
        )
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
def command_rebuild_image_sizes(**kwargs) -> None:
    """Rebuild all content/preview/thumbnail sizes."""
    from omoide.commands.rebuild_image_sizes import cfg
    from omoide.commands.rebuild_image_sizes import run

    db_url = SecretStr(kwargs.pop('db_url'))

    only_users = []
    if kwargs.pop('only_users', ''):
        only_users = utils.split(str(kwargs.pop('only_users', '')))

    config = cfg.Config(db_url=db_url, only_users=only_users, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
            callback=LOG.info, start_template='Rebuilding all image sizes...'
        ):
            run.run(config, database)


@cli.command(name='tree')
@click.option(
    '--db-url',
    required=True,
    help='Database URL',
)
@click.option(
    '--item-uuid',
    type=UUID,
    help='Starting item to show all descendants',
)
@click.option(
    '--show-uuids/--no-show-uuids',
    default=False,
    help='Output items with uuids',
)
def command_tree(**kwargs) -> None:
    """Output all descendants of given item."""
    from omoide.commands.tree import cfg
    from omoide.commands.tree import run

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
            callback=LOG.info, start_template='Showing all descendants...'
        ):
            run.run(config, database)


@cli.command(name='rename_metainfo_key')
@click.option(
    '--db-url',
    required=True,
    help='Database URL',
)
@click.option(
    '--key',
    required=True,
    help='Existing metainfo key',
)
@click.option(
    '--new',
    required=True,
    help='New name for given key',
)
@click.option(
    '--batch-size',
    type=int,
    default=50,
    help='Amount of records to be processed at once',
)
@click.option(
    '--limit',
    type=int,
    default=-1,
    help='Maximum amount of items to process (-1 for infinity)',
)
def command_rename_metainfo_key(
    db_url: str, key: str, new: str, batch_size: int, limit: int
) -> None:
    """Change metainfo key without changing its value."""
    from omoide.commands.rename_metainfo_key import run

    database = sync_db.SyncDatabase(db_url)

    with database.life_cycle():
        with helpers.timing(
            callback=LOG.info, start_template='Changing metainfo key...'
        ):
            run.run(database, key, new, batch_size, limit)


@cli.command(name='move_metainfo_key')
@click.option(
    '--db-url',
    required=True,
    help='Database URL',
)
@click.option(
    '--key',
    required=True,
    help='Existing metainfo key',
)
@click.option(
    '--batch-size',
    type=int,
    default=50,
    help='Amount of records to be processed at once',
)
@click.option(
    '--limit',
    type=int,
    default=-1,
    help='Maximum amount of items to process (-1 for infinity)',
)
def command_move_metainfo_key(
    db_url: str, key: str, batch_size: int, limit: int
) -> None:
    """Move metainfo key to extras."""
    from omoide.commands.move_metainfo_key import run

    database = sync_db.SyncDatabase(db_url)

    with database.life_cycle():
        with helpers.timing(
            callback=LOG.info, start_template=f'Moving metainfo key {key}'
        ):
            run.run(database, key, batch_size, limit)


if __name__ == '__main__':
    cli()
