"""Manual CLI operations.
"""
import asyncio
from typing import Optional
from uuid import UUID

import click
from pydantic import SecretStr

from omoide import utils
from omoide.commands import helpers
from omoide.infra import custom_logging
from omoide.presentation import dependencies as dep
from omoide.storage.database import sync_db

LOG = custom_logging.get_logger(__name__)


@click.group()
def cli():
    """Manual CLI operations."""


@cli.command(
    name='create_user',
)
@click.option(
    '--login',
    required=True,
    help='Login for new user',
)
@click.option(
    '--password',
    required=True,
    help='Password for new user',
)
@click.option(
    '--name',
    default=None,
    help='Name for new user (if not specified will use login)',
)
def cmd_create_user(login: str, password: str, name: Optional[str]) -> None:
    """Manually create user."""
    from omoide.commands.create_user import main
    asyncio.run(main.run(
        authenticator=dep.get_authenticator(),
        items_repo=dep.get_items_write_repo(),
        users_repo=dep.get_users_write_repo(),
        login=login,
        password=password,
        name=name,
    ))


@cli.command(
    name='change_password',
)
@click.option(
    '--uuid',
    required=True,
    help='UUID for existing user',
)
@click.option(
    '--password',
    required=True,
    help='New password',
)
def cmd_change_password(uuid: str, password: str):
    """Manually change password for user."""
    from omoide.commands.change_password import main
    asyncio.run(main.run(
        authenticator=dep.get_authenticator(),
        users_repo=dep.get_users_write_repo(),
        raw_uuid=uuid,
        new_password=password,
    ))


@cli.command(name='rebuild_known_tags')
@click.option(
    '--db-url',
    required=True,
    type=str,
    help='Database URL',
)
@click.option(
    '--anon/--no-anon',
    default=True,
    help='Refresh known tags for anon user',
)
@click.option(
    '--known/--no-known',
    default=True,
    help='Refresh known tags for known users',
)
@click.option(
    '--only-users',
    help='Apply to one or more specially listed users (comma separated)',
)
def command_rebuild_known_tags(**kwargs: str | bool):
    """Refresh cache for known tags."""
    from omoide.commands.rebuild_known_tags import cfg
    from omoide.commands.rebuild_known_tags import run

    db_url = SecretStr(kwargs.pop('db_url'))
    only_users = utils.split(kwargs.pop('only_users', ''))
    config = cfg.Config(db_url=db_url, only_users=only_users, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(callback=LOG.info,
                            start_template='Rebuilding known tags...'):
            run.run(config, database)


@cli.command(name='rebuild_computed_tags')
@click.option(
    '--db-url',
    required=True,
    type=str,
    help='Database URL',
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
def command_rebuild_computed_tags(**kwargs: str | bool):
    """Rebuild all computed tags from the scratch."""
    from omoide.commands.rebuild_computed_tags import cfg
    from omoide.commands.rebuild_computed_tags import run

    db_url = SecretStr(kwargs.pop('db_url'))
    only_users = utils.split(kwargs.pop('only_users', ''))
    config = cfg.Config(db_url=db_url, only_users=only_users, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(callback=LOG.info,
                            start_template='Rebuilding computed tags...'):
            run.run(config, database)


@cli.command(name='compact_tags')
@click.option(
    '--db-url',
    required=True,
    type=str,
    help='Database URL',
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
def cmd_compact_tags(**kwargs: str | bool):
    """If item and its parent share some tags, try to remove duplicates."""
    from omoide.commands.compact_tags import cfg
    from omoide.commands.compact_tags import run

    db_url = SecretStr(kwargs.pop('db_url'))
    only_users = utils.split(kwargs.pop('only_users', ''))
    config = cfg.Config(db_url=db_url, only_users=only_users, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(callback=LOG.info,
                            start_template='Compacting tags...'):
            run.run(config, database)


@cli.command(name='du')
@click.option(
    '--db-url',
    required=True,
    type=str,
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
    only_users = utils.split(kwargs.pop('only_users', ''))
    config = cfg.Config(db_url=db_url, only_users=only_users)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(callback=LOG.info,
                            start_template='Calculating total disk usage...'):
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
    from omoide.commands.force_cover_copying import cfg
    from omoide.commands.force_cover_copying import run

    db_url = SecretStr(kwargs.pop('db_url'))
    only_users = utils.split(kwargs.pop('only_users', ''))
    config = cfg.Config(db_url=db_url, only_users=only_users)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Forcing items to copy thumbnails...',
        ):
            run.run(config, database)


@cli.command(name='refresh_file_sizes_in_db')
@click.option(
    '--db-url',
    required=True,
    type=str,
    help='Database URL',
)
@click.option(
    '--hot-folder',
    type=str,
    default='',
    help='Location of the hot folder (optional)',
    show_default=True,
)
@click.option(
    '--cold-folder',
    type=str,
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
    only_users = utils.split(kwargs.pop('only_users', ''))
    config = cfg.Config(db_url=db_url, only_users=only_users, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Refreshing file sizes for every item...',
        ):
            run.run(config, database)


@cli.command(name='rebuild_image_sizes')
@click.option(
    '--db-url',
    required=True,
    type=str,
    help='Database URL',
)
@click.option(
    '--hot-folder',
    type=str,
    default='',
    help='Location of the hot folder (optional)',
    show_default=True,
)
@click.option(
    '--cold-folder',
    type=str,
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
    only_users = utils.split(kwargs.pop('only_users', ''))
    config = cfg.Config(db_url=db_url, only_users=only_users, **kwargs)
    database = sync_db.SyncDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(callback=LOG.info,
                            start_template='Rebuilding all image sizes...'):
            run.run(config, database)


@cli.command(name='tree')
@click.option(
    '--db-url',
    required=True,
    type=str,
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
        with helpers.timing(callback=LOG.info,
                            start_template='Showing all descendants...'):
            run.run(config, database)


if __name__ == '__main__':
    cli()
