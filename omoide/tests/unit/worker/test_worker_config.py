# -*- coding: utf-8 -*-
"""Tests.
"""
from unittest import mock

import pytest
from click.testing import CliRunner
from pydantic import SecretStr
from pydantic import ValidationError

from omoide.daemons.worker import cfg
from omoide.daemons.worker.__main__ import main


@pytest.fixture
def valid_worker_config_dict():
    return dict(
        name='test',
        db_url=SecretStr('test'),
        hot_folder='test',
        cold_folder='',
        save_hot=True,
        save_cold=False,
        drop_after_saving=False,
        min_interval=5,
        max_interval=300,
        warm_up_coefficient=25.4,
        batch_size=15,
        log_level='NOTSET',
        debug=False,
    )


@pytest.fixture
def valid_worker_config_argv():
    return [
        '--name', 'test',
        '--db-url', 'test',
        '--hot-folder', '/',
        '--save-hot',
    ]


def test_worker_config_correct(valid_worker_config_dict):
    """Must generate valid config."""
    config = cfg.Config(**valid_worker_config_dict)
    assert config is not None
    assert isinstance(config.verbose(), str)


@pytest.mark.parametrize('hot_folder,cold_folder,save_hot,save_cold', [
    ('', '', False, False),
    ('/', '/', False, False),
    ('/', '', False, True),
    ('', '/', True, False),
])
def test_worker_config_folders(
        valid_worker_config_dict,
        hot_folder,
        cold_folder,
        save_hot,
        save_cold,
):
    """Must raise on inadequate combinations."""
    valid_worker_config_dict['hot_folder'] = hot_folder
    valid_worker_config_dict['cold_folder'] = cold_folder
    valid_worker_config_dict['save_hot'] = save_hot
    valid_worker_config_dict['save_cold'] = save_cold

    with pytest.raises(ValidationError):
        cfg.Config(**valid_worker_config_dict)


@pytest.mark.parametrize('min_interval', [0, 9999999999999])
def test_worker_config_min_interval(
        valid_worker_config_dict,
        min_interval,
):
    """Must raise on inadequate min intervals."""
    valid_worker_config_dict['min_interval'] = min_interval

    with pytest.raises(ValidationError):
        cfg.Config(**valid_worker_config_dict)


@pytest.mark.parametrize('min_interval, max_interval', [
    (100, 5),
    (100, 9999999999999),
])
def test_worker_config_max_interval(
        valid_worker_config_dict,
        min_interval,
        max_interval,
):
    """Must raise on inadequate max intervals."""
    valid_worker_config_dict['min_interval'] = min_interval
    valid_worker_config_dict['max_interval'] = max_interval

    with pytest.raises(ValidationError):
        cfg.Config(**valid_worker_config_dict)


@pytest.mark.parametrize('warm_up_coefficient', [0.0, 9999999999999.0])
def test_worker_config_warm_up_coefficient(
        valid_worker_config_dict,
        warm_up_coefficient,
):
    """Must raise on inadequate warm up coefficient."""
    valid_worker_config_dict['warm_up_coefficient'] = warm_up_coefficient

    with pytest.raises(ValidationError):
        cfg.Config(**valid_worker_config_dict)


@pytest.mark.parametrize('batch_size', [0, 9999999999999])
def test_worker_config_batch_size(
        valid_worker_config_dict,
        batch_size,
):
    """Must raise on inadequate batch sizes."""
    valid_worker_config_dict['batch_size'] = batch_size

    with pytest.raises(ValidationError):
        cfg.Config(**valid_worker_config_dict)


def test_worker_config_generation(valid_worker_config_argv):
    """Must create config instance from CLI args."""
    with mock.patch('omoide.daemons.worker.__main__._run') as fake_run:
        runner = CliRunner()
        result = runner.invoke(main, valid_worker_config_argv)  # noqa

    assert result.exit_code == 0
    fake_run.assert_called_once()


def test_worker_config_interrupt(valid_worker_config_argv):
    """Must stop on keyboard interrupt."""
    with mock.patch('omoide.daemons.worker.__main__._run') as fake_run:
        fake_run.side_effect = KeyboardInterrupt
        runner = CliRunner()
        result = runner.invoke(main, valid_worker_config_argv)  # noqa

    assert result.exit_code == 0
    fake_run.assert_called_once()
