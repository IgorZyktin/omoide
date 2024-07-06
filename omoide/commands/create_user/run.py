"""Create user command.
"""
import sqlalchemy as sa

from omoide import const
from omoide import infra
from omoide import utils
from omoide.infra import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(database: SyncDatabase, login: str,
        password: str, name: str | None) -> None:
    """Create new user."""
    with database.start_session() as session:
        authenticator = infra.BcryptAuthenticator(
            complexity=const.AUTH_COMPLEXITY,
        )
        encoded_password = authenticator.encode_password(password)

        stmt = sa.text("""
        SELECT 1 FROM users WHERE uuid = :uuid
        UNION
        SELECT 1 FROM orphan_files WHERE owner_uuid = :uuid;
        """)
        exists = True
        while exists:
            uuid = utils.uuid4()
            exists = bool(session.execute(stmt, {'uuid': str(uuid)}).scalar())

        user = db_models.User(
            uuid=str(utils.uuid4()),  # type: ignore
            login=login,
            password=encoded_password,
            name=name or login,
            root_item=None,
            auth_complexity=const.AUTH_COMPLEXITY,
        )
        session.add(user)
        try:
            session.flush([user])
        except Exception as exc:
            LOG.warning('Failed to create user: {}', exc)
            return

        number = session.execute(sa.func.max(db_models.Item.number)).scalar()

        root_item = db_models.Item(
            uuid=str(utils.uuid4()),  # type: ignore
            parent_uuid=None,
            owner_uuid=user.uuid,
            number=(number or 0) + 1,
            name=user.name,
            is_collection=True,
            content_ext=None,
            preview_ext=None,
            thumbnail_ext=None,
            tags=[],
            permissions=[],
        )
        session.add(root_item)
        session.flush([root_item])

        metainfo = db_models.Metainfo(
            item_uuid=root_item.uuid,
            created_at=utils.now(),
            updated_at=utils.now(),
            deleted_at=None,
            user_time=None,
            content_type=None,
            author=None,
            author_url=None,
            saved_from_url=None,
            description=None,
            extras={},
            content_size=None,
            preview_size=None,
            thumbnail_size=None,
            content_width=None,
            content_height=None,
            preview_width=None,
            preview_height=None,
            thumbnail_width=None,
            thumbnail_height=None,

        )
        session.add(metainfo)
        user.root_item = root_item.uuid
        session.commit()

        LOG.info('Created user {} {}', user.uuid, user.name)
