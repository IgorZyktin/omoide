"""Tests.
"""
from unittest import mock

from click.testing import CliRunner

from omoide.omoide_worker import runtime
from omoide.omoide_worker.__main__ import main


def test_worker_main_once(valid_worker_config):
    """Must run once."""
    fake_worker = mock.Mock()

    with (
        mock.patch('omoide.worker.__main__.worker_config.get_config',
                   return_value=valid_worker_config),
        mock.patch('omoide.worker.__main__.WorkerDatabase'),
        mock.patch('omoide.worker.__main__.Filesystem'),
        mock.patch('omoide.worker.__main__.Worker',
                   return_value=fake_worker),
    ):
        result = CliRunner().invoke(main, ['--once'])  # type: ignore

    # assert
    assert result.exit_code == 0
    fake_worker.download_media.assert_called_once()
    fake_worker.drop_media.assert_called_once()
    fake_worker.copy.assert_called_once()
    fake_worker.drop_copies.assert_called_once()


def test_worker_main_forever(valid_worker_config, dummy_worker_strategy):
    """Must run forever."""
    fake_worker = mock.Mock()

    with (
        mock.patch('omoide.worker.__main__.worker_config.get_config',
                   return_value=valid_worker_config),
        mock.patch('omoide.worker.runtime.get_strategy',
                   return_value=dummy_worker_strategy),
        mock.patch('omoide.worker.__main__.WorkerDatabase'),
        mock.patch('omoide.worker.__main__.Filesystem'),
        mock.patch('omoide.worker.__main__.Worker',
                   return_value=fake_worker),
    ):
        fake_worker.counter = 0
        result = CliRunner().invoke(main, ['--no-once'])  # type: ignore

    # assert
    assert result.exit_code == 0
    fake_worker.download_media.assert_called_once()
    fake_worker.drop_media.assert_called_once()
    fake_worker.copy.assert_called_once()
    fake_worker.drop_copies.assert_called_once()


def test_worker_get_strategy_windows(valid_worker_config):
    """Must return timer base strategy."""
    config = valid_worker_config
    config.strategy = 'SignalStrategy'

    with mock.patch('omoide.worker.runtime.sys') as fake_sys:
        fake_sys.platform = 'win32'
        result = runtime.get_strategy(config)

    assert type(result).__name__ != config.strategy


def test_worker_get_strategy_normal_signal(valid_worker_config):
    """Must return signal base strategy."""
    config = valid_worker_config
    config.strategy = 'SignalStrategy'

    with mock.patch('omoide.worker.runtime.sys') as fake_sys:
        fake_sys.platform = 'linux'
        result = runtime.get_strategy(config)

    assert type(result).__name__ == config.strategy


def test_worker_get_strategy_normal_timer(valid_worker_config):
    """Must return timer base strategy."""
    config = valid_worker_config
    config.strategy = 'TimerStrategy'

    with mock.patch('omoide.worker.runtime.sys') as fake_sys:
        fake_sys.platform = 'linux'
        result = runtime.get_strategy(config)

    assert type(result).__name__ == config.strategy
