"""Tests.
"""
import datetime
import tempfile

import pytest
from pydantic import SecretStr

from omoide.daemons.worker import worker_config


@pytest.fixture
def valid_worker_config_dict():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield dict(
            name='test',
            db_uri=SecretStr('test'),
            db_echo=False,
            hot_folder=tmp_dir,
            cold_folder=None,
            save_hot=True,
            save_cold=False,
            log_level='INFO',
            batch_size=5,
            prefix_size=3,
            run_once=True,
            media=dict(
                should_process=True,
                drop_after=True,
                replication_formula={'test-hot': True, 'test-cold': True}
            ),
            manual_copy=dict(
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
def valid_worker_config(valid_worker_config_dict):
    return worker_config.Config(**valid_worker_config_dict)


@pytest.fixture
def worker_dt():
    return datetime.datetime(
        2022, 12, 2, 20, 10, 15, 128, tzinfo=datetime.timezone.utc)
