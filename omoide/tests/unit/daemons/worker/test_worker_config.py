# -*- coding: utf-8 -*-
"""Tests.
"""
from unittest import mock

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from omoide.daemons.worker import cfg
from omoide.daemons.worker.__main__ import main


def test_worker_config_correct(valid_worker_config_dict):
    """Must generate valid config."""
    config = cfg.Config(**valid_worker_config_dict)
    assert config is not None
    assert isinstance(config.verbose(), str)


@pytest.mark.parametrize('hot_folder,cold_folder,save_hot,save_cold', [
    ('', '', False, False),
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
def test_worker_config_min_interval(valid_worker_config_dict, min_interval):
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
def test_worker_config_batch_size(valid_worker_config_dict, batch_size):
    """Must raise on inadequate batch sizes."""
    valid_worker_config_dict['batch_size'] = batch_size

    with pytest.raises(ValidationError):
        cfg.Config(**valid_worker_config_dict)


def test_worker_is_allowed_to_save(valid_worker_config_dict):
    """Must raise if user wants to save something but cannot."""
    valid_worker_config_dict['media_downloading'] = False
    valid_worker_config_dict['save_hot'] = True
    valid_worker_config_dict['save_cold'] = True

    with pytest.raises(ValidationError):
        cfg.Config(**valid_worker_config_dict)


def test_worker_config_generation(valid_worker_config_argv):
    """Must create config instance from CLI args."""
    with mock.patch('omoide.daemons.worker.__main__.run') as fake_run, \
            mock.patch('omoide.daemons.worker.__main__.Database'):
        runner = CliRunner()
        result = runner.invoke(main, valid_worker_config_argv)  # noqa

    assert result.exit_code == 0
    fake_run.assert_called_once()


def test_worker_config_interrupt(valid_worker_config_argv):
    """Must stop on keyboard interrupt."""
    with mock.patch('omoide.daemons.worker.__main__.run') as fake_run, \
            mock.patch('omoide.daemons.worker.__main__.Database'):
        fake_run.side_effect = KeyboardInterrupt
        runner = CliRunner()
        result = runner.invoke(main, valid_worker_config_argv)  # noqa

    assert result.exit_code == 0
    fake_run.assert_called_once()


def test_worker_config_no_folders_exist(valid_worker_config_dict):
    """Must raise because no folder was found."""
    valid_worker_config_dict['hot_folder'] = 'nonexistent'
    valid_worker_config_dict['cold_folder'] = 'nonexistent'

    with pytest.raises(ValidationError, match='Both hot and cold folders*'):
        cfg.Config(**valid_worker_config_dict)


def test_worker_config_hot_does_not_exist(valid_worker_config_dict):
    """Must raise because hot folder is required and does not exist."""
    existing = valid_worker_config_dict['_existing_folder']

    valid_worker_config_dict['save_hot'] = True
    valid_worker_config_dict['hot_folder'] = 'nonexistent'

    valid_worker_config_dict['save_cold'] = False
    valid_worker_config_dict['cold_folder'] = existing

    with pytest.raises(ValidationError, match='Hot folder does not exist*'):
        cfg.Config(**valid_worker_config_dict)


def test_worker_config_cold_does_not_exist(valid_worker_config_dict):
    """Must raise because cold folder is required and does not exist."""
    existing = valid_worker_config_dict['_existing_folder']

    valid_worker_config_dict['save_hot'] = False
    valid_worker_config_dict['hot_folder'] = existing

    valid_worker_config_dict['save_cold'] = True
    valid_worker_config_dict['cold_folder'] = 'nonexistent'

    with pytest.raises(ValidationError, match='Cold folder does not exist*'):
        cfg.Config(**valid_worker_config_dict)
