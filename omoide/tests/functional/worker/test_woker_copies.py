"""Tests.
"""

import pytest

from omoide import utils
from omoide.worker import runtime
from omoide.worker.filesystem import Filesystem


@pytest.fixture
def populate_database_copies(functional_tests_worker_testing_repo):
    repo = functional_tests_worker_testing_repo

    user_uuid = repo.create_user()
    source_item_uuid = repo.create_item(
        user_uuid,
        thumbnail_size=-1,
        thumbnail_width=4,
        thumbnail_height=8,
    )

    target_item_uuid = repo.create_item(
        user_uuid,
        thumbnail_size=None,
        thumbnail_width=None,
        thumbnail_height=None,
    )

    repo.create_copy_command(
        owner_uuid=user_uuid,
        source_uuid=source_item_uuid,
        target_uuid=target_item_uuid,
        media_type='thumbnail',
    )

    return repo, user_uuid, source_item_uuid, target_item_uuid


@pytest.fixture
def populate_database_ready_command(functional_tests_worker_testing_repo):
    repo = functional_tests_worker_testing_repo

    user_uuid = repo.create_user()
    source_item_uuid = repo.create_item(
        user_uuid,
        thumbnail_size=-1,
        thumbnail_width=4,
        thumbnail_height=8,
    )

    target_item_uuid = repo.create_item(
        user_uuid,
        thumbnail_size=None,
        thumbnail_width=None,
        thumbnail_height=None,
    )

    repo.create_copy_command(
        owner_uuid=user_uuid,
        source_uuid=source_item_uuid,
        target_uuid=target_item_uuid,
        processed_at=utils.now(),
        media_type='thumbnail',
    )

    return repo, user_uuid, source_item_uuid, target_item_uuid


@pytest.fixture
def create_files(
        populate_database_copies,
        functional_tests_worker_config,
        functional_tests_worker,
):
    (repo, user_uuid, source_item_uuid,
     target_item_uuid) = populate_database_copies
    config = functional_tests_worker_config

    filesystem = Filesystem(config)
    filesystem.save_binary(
        user_uuid,
        source_item_uuid,
        'thumbnail',
        'jpg',
        b'something-cool',
    )
    return repo, source_item_uuid, target_item_uuid


def test_worker_copy_thumbnails_only_save(
        create_files,
        functional_tests_worker_config,
        functional_tests_worker,
):
    """Must ensure that copy gets processed."""
    repo, source_item_uuid, target_item_uuid = create_files
    config = functional_tests_worker_config
    worker = functional_tests_worker
    config.media.should_process = False
    config.media.drop_after = False
    config.copy_commands.should_process = True
    config.copy_commands.drop_after = False

    runtime.run_once(config, worker)

    item, metainfo, media, command = repo.get_copy_thumbnail_result(
        target_item_uuid)
    assert item.thumbnail_ext is not None
    assert metainfo.thumbnail_width == 4
    assert metainfo.thumbnail_height == 8
    assert metainfo.thumbnail_size > -1
    assert metainfo.extras['copied_image_from'] == source_item_uuid
    assert len(media) == 1
    assert media[0].content == b'something-cool'
    assert len(media) == 1
    assert len(command) == 1
    assert worker.counter == 1


def test_worker_copy_thumbnails_only_delete(
        populate_database_ready_command,
        functional_tests_worker_config,
        functional_tests_worker,
):
    """Must ensure that copy gets deleted."""
    repo, *_ = populate_database_ready_command
    config = functional_tests_worker_config
    worker = functional_tests_worker
    config.media.should_process = False
    config.media.drop_after = False
    config.copy_commands.should_process = False
    config.copy_commands.drop_after = True

    runtime.run_once(config, worker)

    commands = repo.get_all_thumbnail()
    assert not commands
    assert worker.counter == 1
