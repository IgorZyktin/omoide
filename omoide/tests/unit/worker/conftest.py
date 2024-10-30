"""Tests."""

import datetime
import tempfile

import pytest

from omoide.omoide_worker import interfaces
from omoide.omoide_worker import worker_config


@pytest.fixture()
def valid_worker_config_dict():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield {
            'db_url': 'test',
            'db_echo': False,
            'hot_folder': tmp_dir,
            'cold_folder': None,
            'save_hot': True,
            'save_cold': False,
            'log_level': 'INFO',
            'batch_size': 5,
            'prefix_size': 3,
            'media': {
                'should_process': True,
                'drop_after': True,
            },
            'copy_commands': {
                'should_process': True,
                'drop_after': True,
            },
            'timer_strategy': {
                'min_interval': 5,
                'max_interval': 300,
                'warm_up_coefficient': 25.4,
            },
            'strategy': 'TimerStrategy',
        }


@pytest.fixture()
def valid_worker_config(valid_worker_config_dict):
    return worker_config.Config(**valid_worker_config_dict)


@pytest.fixture()
def dummy_worker_strategy():
    class DummyStrategy(interfaces.AbsStrategy):
        def init(self) -> None:
            pass

        def stop(self) -> None:
            pass

        def wait(self) -> bool:
            return True

        def adjust(self, done_something: bool) -> None:
            pass

    return DummyStrategy()


@pytest.fixture()
def worker_dt():
    return datetime.datetime(2022, 12, 2, 20, 10, 15, 128, tzinfo=datetime.timezone.utc)
