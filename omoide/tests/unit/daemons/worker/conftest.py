# -*- coding: utf-8 -*-
"""Tests.
"""
import pytest
from pydantic import SecretStr


@pytest.fixture
def valid_worker_config_dict():
    return dict(
        name='test',
        db_url=SecretStr('test'),
        hot_folder='test',
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
    )


@pytest.fixture
def valid_worker_config_argv():
    return [
        '--name', 'test',
        '--db-url', 'test',
        '--hot-folder', '/',
        '--save-hot',
        '--download-media',
        '--replication-formula', '{"test-hot": true}'
    ]
