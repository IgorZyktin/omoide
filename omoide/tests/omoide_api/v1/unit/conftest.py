"""Tests."""
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from omoide.omoide_api import application


@pytest.fixture(scope='session')
def fake_config():
    """Return config instance."""
    # TODO - change with real config object
    config = mock.Mock()
    config.env = 'test'
    return config


@pytest.fixture(scope='session')
def api_application(fake_config):
    """Return application instance."""
    # TODO - store config in different folder
    with mock.patch(
        'omoide.presentation.app_config.Config',
        return_value=fake_config,
    ):
        app = application.get_api()
        application.apply_api_routes(app)
        yield app


@pytest.fixture(scope='session')
def api_test_client(api_application):
    """Return client."""
    return TestClient(api_application)
