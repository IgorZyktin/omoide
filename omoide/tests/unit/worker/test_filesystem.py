"""Tests.
"""
import os
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

import pytest

from omoide import utils
from omoide.omoide_worker.filesystem import Filesystem


def test_filesystem_ensure_folder_exists(valid_worker_config):
    """Must create chain of folders."""
    filesystem = Filesystem(valid_worker_config)

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / 'complex' / 'nested' / 'path'
        assert not path.exists()

        # check newly created path
        filesystem.ensure_folder_exists(path)
        assert path.exists()

        # check if path already exist
        filesystem.ensure_folder_exists(path)
        filesystem.ensure_folder_exists(path)
        assert path.exists()


def test_filesystem_safely_save(valid_worker_config, worker_dt):
    """Must save without destroying existing files."""
    filesystem = Filesystem(valid_worker_config)

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / 'saving'

        assert not path.exists()
        filesystem.ensure_folder_exists(path)

        with open(path / 'a.txt', mode='wb') as file:
            file.write(b'initial')

        with mock.patch('omoide.utils.now') as fake_now:
            fake_now.side_effect = [
                worker_dt,
                worker_dt,
                worker_dt + timedelta(seconds=1),
                worker_dt + timedelta(seconds=2),
            ]
            filesystem.safely_save(path, 'a.txt', b'a')
            filesystem.safely_save(path, 'a.txt', b'b')
            new = filesystem.safely_save(path, 'a.txt', b'c')

        assert new == path / 'a.txt'
        assert len(os.listdir(path)) == 4
        with open(path / 'a.txt', mode='rb') as file:
            assert file.read() == b'c'


@pytest.mark.parametrize('filename, reference', [
    ('test', 'test___2022-12-02T20:10:15.000128+00:00'),
    ('test.txt', 'test___2022-12-02T20:10:15.000128+00:00.txt'),
    ('test___.txt', 'test___2022-12-02T20:10:15.000128+00:00.txt'),
    ('test___wtf.txt', 'test___2022-12-02T20:10:15.000128+00:00.txt'),
])
def test_filesystem_make_new_filename(filename, reference, worker_dt,
                                      valid_worker_config):
    """Must alter filename without overwriting it."""
    filesystem = Filesystem(valid_worker_config)

    with mock.patch('omoide.utils.now') as fake_now:
        fake_now.side_effect = [worker_dt, worker_dt + timedelta(seconds=1)]
        new_filename = filesystem.make_new_filename(filename)
        assert new_filename == reference
        assert new_filename != filesystem.make_new_filename(new_filename)


def test_filesystem_load_binary(valid_worker_config):
    """Must load binary data."""
    config = valid_worker_config
    filesystem = Filesystem(config)
    owner_uuid = utils.uuid4()
    item_uuid = utils.uuid4()
    bucket = utils.get_bucket(item_uuid, config.prefix_size)
    filename = f'{item_uuid}.jpg'

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / 'test' / str(owner_uuid) / bucket
        config.hot_folder = tmp_dir
        filesystem.ensure_folder_exists(path)

        with open(path / filename, mode='wb') as file:
            file.write(b'test')

        result = filesystem.load_binary(owner_uuid, item_uuid, 'test', 'jpg')

    assert result == b'test'


def test_filesystem_save_binary(valid_worker_config):
    """Must save binary data."""
    config = valid_worker_config
    filesystem = Filesystem(config)
    owner_uuid = utils.uuid4()
    item_uuid = utils.uuid4()
    bucket = utils.get_bucket(item_uuid, config.prefix_size)
    filename = f'{item_uuid}.jpg'

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / 'test' / str(owner_uuid) / bucket
        config.hot_folder = tmp_dir
        filesystem.ensure_folder_exists(path)

        filesystem.save_binary(owner_uuid, item_uuid, 'test', 'jpg', b'test')

        with open(path / filename, mode='rb') as file:
            assert file.read() == b'test'
