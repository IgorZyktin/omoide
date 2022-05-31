# -*- coding: utf-8 -*-
"""Tests.
"""
import os
from unittest import mock

import pytest

from omoide.presentation import app_config


@pytest.fixture
def ref_config():
    config = mock.Mock()
    config.env = 'test'
    config.db_url = 'fake-db-url'
    config.app.debug = True
    config.app.reload = False
    return config


@pytest.fixture
def fake_env_for_config(ref_config):
    return {
        'OMOIDE_ENV': ref_config.env,
        'OMOIDE_DB_URL': ref_config.db_url,
        'OMOIDE_APP__DEBUG': str(ref_config.app.debug),
        'OMOIDE_APP__RELOAD': str(ref_config.app.reload),

    }


def test_config(fake_env_for_config, ref_config):
    """Must correctly parse env into config."""
    # act
    with mock.patch.dict(os.environ, fake_env_for_config):
        config = app_config.init()

    # assert
    assert config.db_url == ref_config.db_url
    assert config.env == 'test'
    assert config.app.host == '0.0.0.0'
    assert config.app.port == 8080
    assert config.app.injection == ''
    assert config.app.reload == ref_config.app.reload
    assert config.app.debug == ref_config.app.debug
