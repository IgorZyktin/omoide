"""Tests.
"""
import random
import tempfile
from datetime import datetime
from uuid import UUID

import pytest
import sqlalchemy as sa

from omoide import utils
from omoide.storage.database import db_models
from omoide.worker import worker_config
from omoide.worker.database import Database
from omoide.worker.filesystem import Filesystem
from omoide.worker.worker import Worker


@pytest.fixture(scope='session')
def functional_tests_worker_database(functional_tests_db_uri):
    database = Database(db_uri=functional_tests_db_uri, echo=True)
    with database.life_cycle():
        yield database


@pytest.fixture(scope='session')
def functional_tests_worker_config():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield worker_config.Config(
            db_uri='test',
            db_echo=False,
            hot_folder=tmp_dir,
            cold_folder=None,
            save_hot=True,
            save_cold=False,
            log_level='INFO',
            batch_size=5,
            prefix_size=3,
            media=dict(
                should_process=True,
                drop_after=True,
            ),
            copy_thumbnails=dict(
                should_process=True,
                drop_after=True,
            ),
            timer_strategy=dict(
                min_interval=5,
                max_interval=300,
                warm_up_coefficient=25.4,
            ),
            strategy='TimerStrategy',
        )


@pytest.fixture
def functional_tests_worker_filesystem(functional_tests_worker_config):
    return Filesystem(functional_tests_worker_config)


@pytest.fixture
def functional_tests_worker(
        functional_tests_worker_database,
        functional_tests_worker_config,
        functional_tests_worker_filesystem,
):
    database = functional_tests_worker_database
    config = functional_tests_worker_config

    worker = Worker(
        config=config,
        database=database,
        filesystem=Filesystem(config),
    )

    yield worker


class WorkerTestingRepo:
    """Helper class for testing worker."""

    def __init__(self, database: Database) -> None:
        """Initialize instance."""
        self.database = database
        self.items: list[str] = []
        self.users: list[str] = []
        self.copy_thumbnail: list[int] = []

    def create_user(self) -> str:
        """Create test user."""
        with self.database.start_session() as session:
            uuid = str(utils.uuid4())
            user = db_models.User(
                uuid=uuid,
                login='test-for-worker' + str(random.randint(0, 100000)),
                password='test',
                name='test',
                root_item=None,
            )
            session.add(user)
            session.commit()
            self.users.append(uuid)
            return uuid

    def create_item(self, owner_uuid: str, **kwargs) -> str:
        """Create test item."""
        with self.database.start_session() as session:
            item_uuid = str(utils.uuid4())

            item = db_models.Item(
                uuid=item_uuid,
                parent_uuid=None,
                owner_uuid=owner_uuid,
                number=1,
                name='worker-test-item',
                is_collection=False,
                content_ext=None,
                preview_ext=None,
                thumbnail_ext='jpg',
                tags=[],
                permissions=[],
            )

            metainfo = db_models.Metainfo(
                item_uuid=item_uuid,
                created_at=utils.now(),
                updated_at=utils.now(),
                deleted_at=None,
                user_time=None,
                media_type='image/jpg',
                author=None,
                author_url=None,
                saved_from_url=None,
                description=None,
                extras={},
                content_size=None,
                preview_size=None,
                content_width=None,
                content_height=None,
                preview_width=None,
                preview_height=None,
                **kwargs,
            )

            session.add(item)
            session.add(metainfo)
            session.commit()
            self.items.append(item_uuid)
            return item_uuid

    def create_copy_command(
            self,
            owner_uuid: UUID,
            source_uuid: UUID,
            target_uuid: UUID,
            processed_at: datetime | None = None,
    ) -> int:
        """Create test copy commands."""
        with self.database.start_session() as session:
            command = db_models.CommandCopyThumbnail(
                created_at=utils.now(),
                processed_at=processed_at,
                error='',
                owner_uuid=str(owner_uuid),
                source_uuid=str(source_uuid),
                target_uuid=str(target_uuid),
                ext='jpg',
            )
            session.add(command)
            session.commit()
            self.copy_thumbnail.append(command.id)
            return command.id

    def get_copy_thumbnail_result(
            self,
            target_item_uuid: UUID | str,
    ) -> tuple:
        """Create test copy commands."""
        with self.database.start_session() as session:
            item = session.query(db_models.Item).get(target_item_uuid)
            if item is None:
                return None, None, []
            command = session.query(
                db_models.CommandCopyThumbnail
            ).filter(
                db_models.CommandCopyThumbnail.target_uuid == target_item_uuid
            ).all()
            metainfo = item.metainfo
            media = item.media
            return item, metainfo, media, command

    def get_all_thumbnail(self) -> list[db_models.CommandCopyThumbnail]:
        """Create test copy commands."""
        with self.database.start_session() as session:
            commands = session.query(db_models.CommandCopyThumbnail).all()
            return commands

    def drop_all(self) -> None:
        """Remove all created objects."""
        if not self.users:
            return

        # with self.database.start_session() as session:
        #     stmt = sa.delete(
        #         db_models.User
        #     ).where(db_models.User.uuid.in_(self.users))  # type: ignore
        #     session.execute(stmt)
        #     stmt = sa.delete(db_models.Media)
        #     session.execute(stmt)
        #     # stmt = sa.delete(db_models.CommandCopyThumbnail)
        #     # session.execute(stmt)
        #     session.commit()


@pytest.fixture
def functional_tests_worker_testing_repo(functional_tests_worker_database):
    helper = WorkerTestingRepo(functional_tests_worker_database)
    yield helper
    helper.drop_all()
