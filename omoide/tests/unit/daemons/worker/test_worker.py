# -*- coding: utf-8 -*-
"""Tests.
"""
from unittest import mock

import pytest

from omoide.daemons.worker.cfg import Config
from omoide.daemons.worker.filesystem import Filesystem
from omoide.daemons.worker.worker import Worker
from omoide.tests.unit.daemons.worker.fake_database import FakeDatabase


@pytest.mark.parametrize('hot, cold, reference', [
    (True, False, [mock.ANY]),
    (False, True, [mock.ANY]),
    (True, True, [mock.ANY, mock.ANY]),
])
def test_worker_get_folders(hot, cold, reference, valid_worker_config_dict):
    """Must return iterator on folders."""
    existing = valid_worker_config_dict['_existing_folder']
    valid_worker_config_dict['save_hot'] = hot
    valid_worker_config_dict['save_cold'] = cold

    if hot:
        valid_worker_config_dict['hot_folder'] = existing
    else:
        valid_worker_config_dict['hot_folder'] = 'nonexistent'

    if cold:
        valid_worker_config_dict['cold_folder'] = existing
    else:
        valid_worker_config_dict['cold_folder'] = 'nonexistent'

    worker = Worker(Config(**valid_worker_config_dict), Filesystem())
    assert list(worker.get_folders()) == reference


def test_worker_formula(valid_worker_config_dict):
    """Must return valid worker formula."""
    valid_worker_config_dict['save_hot'] = True
    valid_worker_config_dict['save_cold'] = False

    worker = Worker(Config(**valid_worker_config_dict), Filesystem())
    assert worker.formula == {
        'test-hot': True,
        'test-cold': False,
    }


def test_worker_adjust_interval(valid_worker_config_dict):
    """Must ensure that we have decay in sleep interval."""
    valid_worker_config_dict['min_interval'] = 2.0
    valid_worker_config_dict['max_interval'] = 100.0
    valid_worker_config_dict['warm_up_coefficient'] = 3.0

    worker = Worker(Config(**valid_worker_config_dict), Filesystem())

    assert pytest.approx(worker.adjust_interval(0)) == 100.0
    assert pytest.approx(worker.adjust_interval(0)) == 100.0
    assert pytest.approx(worker.adjust_interval(0)) == 100.0
    assert pytest.approx(worker.adjust_interval(1)) == 2.0
    assert pytest.approx(worker.adjust_interval(0)) == 6.0
    assert pytest.approx(worker.adjust_interval(0)) == 18.0
    assert pytest.approx(worker.adjust_interval(0)) == 54.0
    assert pytest.approx(worker.adjust_interval(0)) == 100.0
    assert pytest.approx(worker.adjust_interval(0)) == 100.0


def test_worker_download_media(valid_worker_config):
    """Must check that all media related operations work."""
    # arrange
    worker = Worker(valid_worker_config, mock.Mock())
    database = FakeDatabase()

    database.get_media_ids.return_value = [1, 2, 3, 4, 5]

    # act
    total = worker.download_media(mock.Mock(), database)

    # assert
    assert total == 2

    database.assert_has_calls([
        mock.call.session.commit(),
        mock.call.session.commit(),
    ])

    # noinspection PyUnresolvedReferences
    worker.filesystem.assert_has_calls([
        mock.call.ensure_folder_exists(*[mock.ANY] * 5),
        mock.call.safely_save(*[mock.ANY] * 4),
        mock.call.ensure_folder_exists(*[mock.ANY] * 5),
        mock.call.safely_save(*[mock.ANY] * 4),
    ])


def test_worker_manual_copy(valid_worker_config):
    """Must check that all copy operations work."""
    # arrange
    worker = Worker(valid_worker_config, mock.Mock())
    database = FakeDatabase()

    database.get_manual_copy_targets.return_value = [1, 2, 3, 4, 5]

    # act
    total = worker.manual_copy(mock.Mock(), database)

    # assert
    assert total == 3

    database.assert_has_calls([
        mock.call.get_manual_copy_targets(mock.ANY),
        mock.call.session.add(mock.ANY),
        mock.call.session.commit(),
        mock.call.session.add(mock.ANY),
        mock.call.session.commit(),
        mock.call.session.add(mock.ANY),
        mock.call.session.commit(),
    ])

    # noinspection PyUnresolvedReferences
    worker.filesystem.assert_has_calls([
        mock.call.load_from_filesystem(*[mock.ANY] * 6),
        mock.call.load_from_filesystem(*[mock.ANY] * 6),
        mock.call.load_from_filesystem(*[mock.ANY] * 6),
    ])


def test_worker_drop_media(valid_worker_config):
    """Must check that worker calls database."""
    worker = Worker(valid_worker_config, mock.Mock())
    database = FakeDatabase()
    database.drop_media.return_value = 1

    # act
    total = worker.drop_media(mock.Mock(), database)

    # assert
    assert total == 1
    database.drop_media.assert_called_once()


def test_worker_drop_manual_copies(valid_worker_config):
    """Must check that worker calls database."""
    worker = Worker(valid_worker_config, mock.Mock())
    database = FakeDatabase()
    database.drop_manual_copies.return_value = 1

    # act
    total = worker.drop_manual_copies(mock.Mock(), database)

    # assert
    assert total == 1
    database.drop_manual_copies.assert_called_once()
