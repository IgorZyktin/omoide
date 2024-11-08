"""Tests."""

from unittest import mock

from click.testing import CliRunner

from omoide.omoide_worker.__main__ import main


def test_worker_main_once(valid_worker_config):
    """Must run once."""
    fake_worker = mock.Mock()

    with (
        mock.patch(
            'omoide.omoide_worker.__main__.worker_config.get_config',
            return_value=valid_worker_config,
        ),
        mock.patch('omoide.omoide_worker.__main__.WorkerDatabase'),
        mock.patch('omoide.omoide_worker.__main__.Filesystem'),
        mock.patch('omoide.omoide_worker.__main__.Worker', return_value=fake_worker),
    ):
        result = CliRunner().invoke(main, ['--once'])

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
        mock.patch(
            'omoide.omoide_worker.__main__.worker_config.get_config',
            return_value=valid_worker_config,
        ),
        mock.patch(
            'omoide.omoide_worker.runtime.get_strategy',
            return_value=dummy_worker_strategy,
        ),
        mock.patch('omoide.omoide_worker.__main__.WorkerDatabase'),
        mock.patch('omoide.omoide_worker.__main__.Filesystem'),
        mock.patch('omoide.omoide_worker.__main__.Worker', return_value=fake_worker),
    ):
        fake_worker.counter = 0
        result = CliRunner().invoke(main, ['--no-once'])

    # assert
    assert result.exit_code == 0
    fake_worker.download_media.assert_called_once()
    fake_worker.drop_media.assert_called_once()
    fake_worker.copy.assert_called_once()
    fake_worker.drop_copies.assert_called_once()
