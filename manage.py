# -*- coding: utf-8 -*-
"""Manual CLI operations.
"""
from typing import Optional

import click


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
    print(locals())


if __name__ == '__main__':
    cli()
