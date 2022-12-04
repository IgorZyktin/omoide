# -*- coding: utf-8 -*-
"""Manual CLI operations.
"""
import asyncio
from typing import Optional
from uuid import UUID

import click

from omoide.commands.common import base_db
from omoide.commands.common import helpers
from omoide.infra import custom_logging
from omoide.presentation import dependencies as dep


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
