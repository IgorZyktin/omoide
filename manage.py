# -*- coding: utf-8 -*-
"""Manual CLI operations.
"""
import asyncio
from typing import Optional
from uuid import UUID

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
        items_repo=dep.items_write_repository,
        users_repo=dep.users_write_repository,
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
        users_repo=dep.users_write_repository,
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
    from omoide.commands.application.refresh_known_tags import main, cfg

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Refreshing known tags...',
        ):
            main.run(config=config, database=database)


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
    '--output-items/--no-output-items',
    default=True,
    help='Output every refreshed item',
)
def cmd_refresh_tags(**kwargs: str | bool):
    """If item and its parent share some tags, try to remove duplicates."""
    from omoide.commands.application.compact_tags import main, cfg

    db_url = SecretStr(kwargs.pop('db_url'))
    config = cfg.Config(db_url=db_url, **kwargs)
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle():
        with helpers.timing(
                callback=LOG.info,
                start_template='Compacting tags...',
        ):
            main.run(config=config, database=database)

# Filesystem related commands -------------------------------------------------


@cli.command(
    name='du',
)
def cmd_du():
    """Show disk usage for every user."""
    from omoide.commands.filesystem.du import cfg, run

    config = cfg.get_config()
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle() as engine:
        with helpers.timing(
                start_template='Calculating total disk usage...',
        ):
            run.main(engine, config)


@cli.command(
    name='refresh_size',
)
@click.option(
    '--limit',
    type=int,
    default=-1,
    help='Maximum amount of items to process (-1 for infinity)',
)
@click.option(
    '--marker',
    type=UUID,
    default=None,
    help='Item from which we should start',
)
def cmd_refresh_size(limit: int, marker: Optional[UUID]):
    """Recalculate storage size for every item."""
    from omoide.commands.filesystem.refresh_size import cfg, run

    config = cfg.get_config()
    database = base_db.BaseDatabase(config.db_url.get_secret_value())

    with database.life_cycle() as engine:
        with helpers.timing(
                start_template='Refreshing actual disk usage...',
        ):
            config.limit = limit
            config.marker = marker
            run.main(engine, config)


if __name__ == '__main__':
    cli()
