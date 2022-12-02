# -*- coding: utf-8 -*-
"""Tests.
"""
import datetime
import tempfile

import pytest
from pydantic import SecretStr

from omoide.daemons.worker import cfg


@pytest.fixture
def valid_worker_config_dict():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield dict(
            name='test',
            db_url=SecretStr('test'),
            hot_folder=tmp_dir,
            cold_folder='',
            save_hot=True,
            save_cold=False,
            download_media=True,
            manual_copy=True,
            drop_done_media=False,
            drop_done_copies=False,
            min_interval=5,
            max_interval=300,
            warm_up_coefficient=25.4,
            batch_size=15,
            log_level='NOTSET',
            debug=False,
            prefix_size=3,
            single_run=False,
            echo=False,
            replication_formula={'test-hot': True, 'test-cold': True},
            _existing_folder=tmp_dir,
        )


@pytest.fixture
def valid_worker_config(valid_worker_config_dict):
    return cfg.Config(**valid_worker_config_dict)


@pytest.fixture
def valid_worker_config_argv():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield [
            '--name', 'test',
            '--db-url', 'test',
            '--hot-folder', tmp_dir,
            '--save-hot',
            '--download-media',
            '--replication-formula', '{"test-hot": true}'
        ]


@pytest.fixture
def worker_dt():
    return datetime.datetime(
        2022, 12, 2, 20, 10, 15, 128, tzinfo=datetime.timezone.utc)
