"""Change password command.
"""
from omoide import utils
from omoide.domain import interfaces
from omoide.infra import custom_logging

LOG = custom_logging.get_logger(__name__)


async def run(
        authenticator: interfaces.AbsAuthenticator,
        users_repo: interfaces.AbsUsersWriteRepository,
        raw_uuid: str,
        new_password: str,
) -> None:
    """Execute command."""
    uuid = utils.cast_uuid(raw_uuid)

    if not uuid:
        raise ValueError(f'Wrong uuid value given: {raw_uuid!r}')

    LOG.info('Changing password for user: {}', uuid)

    try:
        await users_repo.db.connect()
        user = await users_repo.read_user(uuid)

        if user is None:
            LOG.error('User with uuid {} does not exist', uuid)

        else:
            user.password = authenticator.encode_password(new_password)
            await users_repo.update_user(user)
            LOG.info('Changed password for user {} {}',
                     user.uuid, user.name)
    finally:
        await users_repo.db.disconnect()
