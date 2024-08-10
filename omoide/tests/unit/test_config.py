"""Tests."""

import os
from unittest import mock

import pytest

from omoide.presentation import app_config


@pytest.fixture
def ref_config():
    config = mock.Mock()
    config.env = 'test'
    config.db_url_app = 'fake-db-url'
    return config


@pytest.fixture
def fake_env_for_config(ref_config):
    return {
        'OMOIDE_ENV': ref_config.env,
        'OMOIDE_DB_URL_APP': ref_config.db_url_app,
    }


def test_config(fake_env_for_config, ref_config):
    """Must correctly parse env into config."""
    # act
    with mock.patch.dict(os.environ, fake_env_for_config):
        config = app_config.Config()

    # assert
    assert config.db_url_app.get_secret_value() == ref_config.db_url_app
    assert config.env == 'test'
