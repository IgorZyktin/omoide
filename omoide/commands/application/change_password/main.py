# -*- coding: utf-8 -*-
"""Change password command.
"""
from omoide import utils
from omoide.domain import interfaces
from omoide.infra.custom_logging import Logger


async def run(
        logger: Logger,
        authenticator: interfaces.AbsAuthenticator,
        users_repo: interfaces.AbsUsersWriteRepository,
        raw_uuid: str,
        new_password: str,
) -> None:
    """Execute command."""
    uuid = utils.cast_uuid(raw_uuid)

    if not uuid:
        raise ValueError(f'Wrong uuid value given: {raw_uuid!r}')

    logger.info('Changing password for user: {}', uuid)

    try:
        await users_repo.db.connect()
        user = await users_repo.read_user(uuid)

        if user is None:
            logger.error('User with uuid {} does not exist', uuid)

        else:
            user.password = authenticator.encode_password(new_password)
            await users_repo.update_user(user)
            logger.info('Changed password for user {} {}',
                        user.uuid, user.name)
    finally:
        await users_repo.db.disconnect()
