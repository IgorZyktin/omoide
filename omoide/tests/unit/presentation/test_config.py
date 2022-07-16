# -*- coding: utf-8 -*-
"""Tests.
"""
import os
from unittest import mock
from uuid import UUID

import pytest

from omoide.presentation import app_config


@pytest.fixture
def ref_config():
    config = mock.Mock()
    config.env = 'test'
    config.db_url = 'fake-db-url'
    config.test_users = frozenset([
        UUID('07c693ef-fb26-42f8-aea2-3275a45828bb'),
        UUID('f4986873-c10a-4770-8059-3558add8846c'),
    ])
    return config


@pytest.fixture
def fake_env_for_config(ref_config):
    return {
        'OMOIDE_ENV': ref_config.env,
        'OMOIDE_DB_URL': ref_config.db_url,
        'OMOIDE_TEST_USERS': ','.join(map(str, ref_config.test_users)),
    }


def test_config(fake_env_for_config, ref_config):
    """Must correctly parse env into config."""
    # act
    with mock.patch.dict(os.environ, fake_env_for_config):
        config = app_config.init()

    # assert
    assert config.db_url.get_secret_value() == ref_config.db_url
    assert config.env == 'test'
