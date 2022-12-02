# -*- coding: utf-8 -*-
"""Tests.
"""
import os
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

import pytest

from omoide.daemons.worker.filesystem import Filesystem


def test_filesystem_ensure_folder_exists():
    """Must create chain of folders."""
    arg = ['some', 'complex', 'nested', 'path']
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir).joinpath(*arg)
        assert not path.exists()

        # check newly created path
        Filesystem().ensure_folder_exists(mock.Mock(), tmp_dir, *arg)
        assert path.exists()

        # check if path already exist
        Filesystem().ensure_folder_exists(mock.Mock(), tmp_dir, *arg)
        Filesystem().ensure_folder_exists(mock.Mock(), tmp_dir, *arg)
        assert path.exists()


def test_filesystem_safely_save(worker_dt):
    """Must save without destroying existing files."""
    filesystem = Filesystem()

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / 'a.txt'

        assert not path.exists()

        with open(path, mode='wb') as file:
            file.write(b'initial')

        with mock.patch('omoide.utils.now') as fake_now:
            fake_now.side_effect = [
                worker_dt,
                worker_dt,
                worker_dt + timedelta(seconds=1),
                worker_dt + timedelta(seconds=2),
            ]
            filesystem.safely_save(
                mock.Mock(), Path(tmp_dir), 'a.txt', b'a')
            filesystem.safely_save(
                mock.Mock(), Path(tmp_dir), 'a.txt', b'b')
            new = filesystem.safely_save(
                mock.Mock(), Path(tmp_dir), 'a.txt', b'c')

        assert filesystem.load_from_filesystem(new) == b'c'
        assert len(os.listdir(tmp_dir)) == 4
        assert new == path


@pytest.mark.parametrize('filename, reference', [
    ('test', 'test___2022-12-02T20:10:15.000128+00:00'),
    ('test.txt', 'test___2022-12-02T20:10:15.000128+00:00.txt'),
    ('test___.txt', 'test___2022-12-02T20:10:15.000128+00:00.txt'),
    ('test___wtf.txt', 'test___2022-12-02T20:10:15.000128+00:00.txt'),
])
def test_filesystem_make_new_filename(filename, reference, worker_dt):
    """Must alter filename without overwriting it."""
    with mock.patch('omoide.utils.now') as fake_now:
        fake_now.side_effect = [worker_dt, worker_dt + timedelta(seconds=1)]
        new_filename = Filesystem().make_new_filename(filename)
        assert new_filename == reference
        assert new_filename != Filesystem().make_new_filename(new_filename)


def test_filesystem_load_from_filesystem():
    """Must load binary data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / 'a.txt'

        assert not path.exists()

        with open(path, mode='wb') as file:
            file.write(b'test')

        assert path.exists()
        assert Filesystem().load_from_filesystem(tmp_dir, 'a.txt') == b'test'
