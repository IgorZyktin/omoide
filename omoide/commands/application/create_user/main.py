# -*- coding: utf-8 -*-
"""Create user command.
"""
from typing import Optional

from omoide import use_cases
from omoide.domain import interfaces
from omoide.infra.custom_logging import Logger
from omoide.infra.special_types import Failure
from omoide.presentation import api_models


async def run(
        logger: Logger,
        authenticator: interfaces.AbsAuthenticator,
        items_repo: interfaces.AbsItemsWriteRepository,
        users_repo: interfaces.AbsUsersWriteRepository,
        login: str,
        password: str,
        name: Optional[str],
) -> None:
    """Execute command."""
    use_case = use_cases.CreateUserUseCase(items_repo, users_repo)
    raw_user = api_models.CreateUserIn(
        uuid=None,
        root_item=None,
        login=login,
        password=password,
        name=name,
    )

    logger.info('Creating new user: {}', name or login)

    try:
        await users_repo.db.connect()
        result = await use_case.execute(authenticator, raw_user)

        if isinstance(result, Failure):
            logger.error('Failed to create new user: {}', result.error)
        else:
            logger.info('Created user with UUID: {}', result.value)

    finally:
        await users_repo.db.disconnect()
