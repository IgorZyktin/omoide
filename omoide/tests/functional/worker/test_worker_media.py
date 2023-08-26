"""Tests.
"""
import pytest

from omoide import utils
from omoide.worker import runtime
from omoide.worker.filesystem import Filesystem


@pytest.fixture
def populate_database_media(functional_tests_worker_testing_repo):
    repo = functional_tests_worker_testing_repo

    user_uuid = repo.create_user()
    item_uuid = repo.create_item(user_uuid)

    repo.create_media(
        owner_uuid=user_uuid,
        item_uuid=item_uuid,
        media_type='thumbnail',
        content=b'event-cooler',
    )

    return repo, user_uuid, item_uuid


@pytest.fixture
def populate_database_ready_media(functional_tests_worker_testing_repo):
    repo = functional_tests_worker_testing_repo

    user_uuid = repo.create_user()
    item_uuid = repo.create_item(user_uuid)

    repo.create_media(
        owner_uuid=user_uuid,
        item_uuid=item_uuid,
        media_type='thumbnail',
        content=b'even-cooler',
        processed_at=utils.now(),
    )

    return repo, user_uuid, item_uuid


def test_worker_media_only_save(
        populate_database_media,
        functional_tests_worker_config,
        functional_tests_worker,
):
    """Must ensure that media gets processed."""
    repo, user_uuid, item_uuid = populate_database_media
    config = functional_tests_worker_config
    worker = functional_tests_worker
    filesystem = Filesystem(config)
    config.media.should_process = True
    config.media.drop_after = False
    config.copy_thumbnails.should_process = False
    config.copy_thumbnails.drop_after = False

    runtime.run_once(config, worker)

    content = filesystem.load_binary(
        owner_uuid=user_uuid,
        item_uuid=item_uuid,
        target_folder='thumbnail',
        ext='jpg',
    )
    assert content == b'event-cooler'


def test_worker_media_only_delete(
        populate_database_ready_media,
        functional_tests_worker_config,
        functional_tests_worker,
):
    """Must ensure that media gets deleted."""
    repo, *_ = populate_database_ready_media
    config = functional_tests_worker_config
    worker = functional_tests_worker
    config.media.should_process = True
    config.media.drop_after = False
    config.copy_thumbnails.should_process = False
    config.copy_thumbnails.drop_after = False

    runtime.run_once(config, worker)

    media = repo.get_all_media()
    assert not media
    assert worker.counter == 1
