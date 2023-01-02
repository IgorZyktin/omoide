# -*- coding: utf-8 -*-
"""Manual CLI operations.
"""
import asyncio
from typing import Optional

import click
from pydantic import SecretStr

from omoide.commands.common import base_db
from omoide.commands.common import helpers
from omoide.infra import custom_logging
from omoide.presentation import dependencies as dep

LOG = custom_logging.get_logger(__name__)


@click.group()
def cli():
    """Manual CLI operations."""


# Application related commands ------------------------------------------------


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
    from omoide.commands.application.create_user import main
    asyncio.run(main.run(
        logger=custom_logging.get_logger(__name__),
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
    from omoide.commands.application.change_password import main
    asyncio.run(main.run(
        logger=custom_logging.get_logger(__name__),
        authenticator=dep.get_authenticator(),
        users_repo=dep.get_users_write_repo(),
        raw_uuid=uuid,
        new_password=password,
    ))


@cli.command(
    name='refresh_known_tags',
)
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
    '--only-user',
    help='Refresh known tags specifically for this user',
)
def cmd_refresh_known_tags(**kwargs: str | bool):
    """Refresh cache for known tags."""
    from omoide.commands.application.refresh_known_tags import cfg
    from omoide.commands.application.refresh_known_tags import run

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Refreshing known tags...',
        ):
            run.run(config=config, database=database)


@cli.command(
    name='refresh_tags',
)
@click.option(
    '--db-url',
    required=True,
    type=str,
    help='Database URL',
)
@click.option(
    '--only-user',
    help='Refresh tags specifically for this user',
)
@click.option(
    '--output-items/--no-output-items',
    default=True,
    help='Output every refreshed item',
)
def cmd_refresh_tags(**kwargs: str | bool):
    """Refresh all tags."""
    from omoide.commands.application.refresh_tags import main, cfg

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Refreshing tags...',
        ):
            main.run(config=config, database=database)


@cli.command(
    name='compact_tags',
)
@click.option(
    '--db-url',
    required=True,
    type=str,
    help='Database URL',
)
@click.option(
    '--only-user',
    help='Refresh tags specifically for this user',
)
@click.option(
    '--log-every-item/--no-log-every-item',
    default=False,
    help='Output every refreshed item',
)
@click.option(
    '--output-items/--no-output-items',
    default=True,
    help='Output every refreshed item',
)
def cmd_compact_tags(**kwargs: str | bool):
    """If item and its parent share some tags, try to remove duplicates."""
    from omoide.commands.application.compact_tags import cfg
    from omoide.commands.application.compact_tags import run

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Compacting tags...',
        ):
            run.run(database, config)


@cli.command(
    name='du',
)
@click.option(
    '--db-url',
    required=True,
    type=str,
    help='Database URL',
)
@click.option(
    '--only-user',
    help='Show disk usage for a single user',
)
def cmd_du(**kwargs) -> None:
    """Show disk usage for every user."""
    from omoide.commands.application.du import cfg
    from omoide.commands.application.du import run

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Calculating total disk usage...',
        ):
            run.run(database, config)


@cli.command(
    name='force_collections_to_copy_cover',
)
@click.option(
    '--db-url',
    required=True,
    help='Database URL',
)
@click.option(
    '--api-endpoint',
    default=None,
    help='Where to send command with mutation operations',
    show_default=True,
)
@click.option(
    '--only-user',
    help='Refresh tags specifically for this user',
)
@click.option(
    '--log-every-item/--no-log-every-item',
    default=False,
    help='Output every refreshed item',
)
def cmd_force_collections_to_copy_cover(**kwargs) -> None:
    """Force collections to explicitly write origins of their covers."""
    from omoide.commands.application.force_collections_to_copy_cover import cfg
    from omoide.commands.application.force_collections_to_copy_cover import run

    if not kwargs.get('api_endpoint'):
        raise RuntimeError('You have to specify URL for active API')

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Forcing items to copy covers...',
        ):
            run.run(database, config)


# Filesystem related commands -------------------------------------------------


@cli.command(
    name='refresh_file_sizes_in_db',
)
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
    '--only-user',
    help='Refresh tags specifically for this user',
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
def cmd_refresh_file_sizes_in_db(**kwargs) -> None:
    """Recalculate all file sizes for every item."""
    from omoide.commands.filesystem.refresh_file_sizes_in_db import cfg
    from omoide.commands.filesystem.refresh_file_sizes_in_db import run

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                start_template='Refreshing file sizes for every item...',
        ):
            run.run(database, config)


if __name__ == '__main__':
    cli()
