# -*- coding: utf-8 -*-
"""Tests.
"""
from unittest import mock

import pytest

from omoide.daemons.worker.__main__ import do_stuff
from omoide.daemons.worker.__main__ import run
from omoide.daemons.worker.cfg import Config
from omoide.daemons.worker.filesystem import Filesystem
from omoide.daemons.worker.worker import Worker
from omoide.tests.unit.daemons.worker.fake_database import FakeDatabase


def test_worker_run_oneshot_bad(valid_worker_config_dict):
    """Must run once."""
    valid_worker_config_dict['single_run'] = True
    worker = Worker(Config(**valid_worker_config_dict), Filesystem())
    database = FakeDatabase()

    with mock.patch('omoide.daemons.worker.__main__.do_stuff') as fake_do:
        fake_do.side_effect = ValueError
        run(mock.Mock(), database, worker)

    # assert
    fake_do.assert_called()


def test_worker_run_oneshot_good(valid_worker_config_dict):
    """Must run once."""
    valid_worker_config_dict['single_run'] = True
    worker = Worker(Config(**valid_worker_config_dict), Filesystem())
    database = FakeDatabase()

    with mock.patch('omoide.daemons.worker.__main__.do_stuff') as fake_do:
        fake_do.return_value = 1
        run(mock.Mock(), database, worker)

    # assert
    fake_do.assert_called()


def test_worker_run_oneshot_exc(valid_worker_config_dict):
    """Must run once."""
    valid_worker_config_dict['single_run'] = False
    worker = Worker(Config(**valid_worker_config_dict), Filesystem())
    database = FakeDatabase()

    with mock.patch('omoide.daemons.worker.__main__.do_stuff') as fake_do:
        with mock.patch('omoide.daemons.worker.__main__.time') as fake_time:
            fake_do.return_value = 1
            fake_time.sleep.side_effect = ValueError

            with pytest.raises(ValueError):
                run(mock.Mock(), database, worker)

    # assert
    fake_do.assert_called()


@pytest.mark.parametrize(
    'download_media, drop_done_media, '
    'manual_copy, drop_done_copies, reference', [
        (False, False, False, False, 0),
        (True, False, False, False, 1),
        (True, True, False, False, 2),
        (False, True, False, False, 0),
        (False, False, True, False, 1),
        (False, False, True, True, 2),
        (False, False, False, True, 0),
    ]
)
def test_worker_du_stuff(
        valid_worker_config_dict,
        download_media,
        drop_done_media,
        manual_copy,
        drop_done_copies,
        reference,
):
    """Must invoke do_stuff paths."""
    worker = mock.Mock()
    worker.config.download_media = download_media
    worker.config.drop_done_media = drop_done_media
    worker.config.manual_copy = manual_copy
    worker.config.drop_done_copies = drop_done_copies

    worker.download_media.return_value = 1
    worker.drop_media.return_value = 1
    worker.manual_copy.return_value = 1
    worker.drop_manual_copies.return_value = 1

    operations = do_stuff(mock.Mock(), mock.Mock(), worker)
    assert operations == reference
