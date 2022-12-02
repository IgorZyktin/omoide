# -*- coding: utf-8 -*-
"""Manual CLI operations.
"""
import asyncio
from typing import Optional
from uuid import UUID

import click

from omoide.commands.common import base_db
from omoide.commands.common import helpers
from omoide.infra.special_types import Failure
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep
from omoide.storage.repositories.asyncpg.rp_users import UsersRepository
from omoide.use_cases import CreateUserUseCase


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
def cmd_create_user(login: str, password: str, name: Optional[str]):
    """Manually create user."""
    use_case = CreateUserUseCase(
        items_repo=dep.items_write_repository,
        users_repo=UsersRepository(dep.db),
    )

    raw_user = api_models.CreateUserIn(
        login=login,
        password=password,
        name=name,
    )

    async def _coro():
        print('Going to create new user')
        await dep.db.connect()
        result = await use_case.execute(dep.get_authenticator(), raw_user)
        await dep.db.disconnect()

        if isinstance(result, Failure):
            print(str(result.error))
        else:
            print(result.value)

    asyncio.run(_coro())


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
    users_repo = UsersRepository(dep.db)

    async def _coro():
        print(f'Going to change password for user {uuid}')
        await dep.db.connect()
        user = await users_repo.read_user(UUID(uuid))
        if user is None:
            print(f'User with uuid {uuid} does not exist')
            return

        user.password = dep.get_authenticator().encode_password(
            password.encode()).decode()

        await users_repo.update_user(user)
        await dep.db.disconnect()
        print(f'Successfully changed password for {user.uuid} {user.name}')

    asyncio.run(_coro())


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
