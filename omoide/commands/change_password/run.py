"""Change user password command.
"""
from uuid import UUID

from omoide import const
from omoide import infra
from omoide.infra import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(database: SyncDatabase, uuid: UUID, password: str) -> None:
    """Change password for existing user."""
    with database.start_session() as session:
        user = session.query(db_models.User).get(str(uuid))

        if user is None:
            LOG.error('There is no user with UUID {}', uuid)
            return

        authenticator = infra.BcryptAuthenticator(
            complexity=const.AUTH_COMPLEXITY,
        )

        encoded_password = authenticator.encode_password(password)
        user.password = encoded_password
        user.auth_complexity = const.AUTH_COMPLEXITY
        session.commit()

        LOG.info('Changed password for user {} {}', user.uuid, user.name)
