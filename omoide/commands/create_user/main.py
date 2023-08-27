"""Create user command.
"""
from omoide import use_cases
from omoide.domain import interfaces
from omoide.infra import custom_logging
from omoide.infra.special_types import Failure
from omoide.presentation import api_models

LOG = custom_logging.get_logger(__name__)


async def run(
        authenticator: interfaces.AbsAuthenticator,
        items_repo: interfaces.AbsItemsWriteRepository,
        users_repo: interfaces.AbsUsersWriteRepository,
        login: str,
        password: str,
        name: str | None,
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

    LOG.info('Creating new user: {}', name or login)

    try:
        await users_repo.db.connect()
        result = await use_case.execute(authenticator, raw_user)

        if isinstance(result, Failure):
            LOG.error('Failed to create new user: {}', result.error)
        else:
            LOG.info('Created user with UUID: {}', result.value)

    finally:
        await users_repo.db.disconnect()
