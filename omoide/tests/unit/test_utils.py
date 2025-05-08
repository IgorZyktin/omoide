"""Tests."""

from uuid import UUID

import pytest

from omoide import utils


@pytest.mark.parametrize(
    ('uuid', 'length', 'result'),
    [
        ('fb6a8840-d6a8-4ab4-9555-be67917c8717', 2, 'fb'),
        (UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717'), 3, 'fb6'),
    ],
)
def test_get_bucket(uuid, length, result):
    """Must cut symbols from the start, but only if input is UUID."""
    assert utils.get_bucket(uuid, length) == result
