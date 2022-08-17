# -*- coding: utf-8 -*-
"""Manual CLI operations.
"""
import asyncio
from typing import Optional

import click

from omoide.presentation import api_models
from omoide.presentation import dependencies as dep
from omoide.storage.repositories.rp_users import UsersRepository
from omoide.use_cases.api import uc_users


@click.group()
def cli():
    """Manual CLI operations."""


@cli.command(name='create_user')
@click.option('--login', required=True, help='Login for new user')
@click.option('--password', required=True, help='Password for new user')
@click.option('--name', default=None,
              help='Name for new user (if not specified will use login)')
def cmd_create_user(login: str, password: str, name: Optional[str]):
    """Manually create user."""
    use_case = uc_users.CreateUserUseCase(
        items_repo=dep.items_repository,
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
        uuid = await use_case.execute(dep.current_authenticator, raw_user)
        await dep.db.disconnect()
        print(uuid)

    asyncio.run(_coro())


if __name__ == '__main__':
    cli()
