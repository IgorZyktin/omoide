# -*- coding: utf-8 -*-
"""Tests.
"""
from uuid import UUID

import pytest

from omoide import utils


@pytest.mark.parametrize('uuid,result', [
    ('something', False),
    (UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717'), True),
    ('fb6a8840-d6a8-4ab4-9555-be67917c8717', True),
])
def test_is_valid_uuid(uuid, result):
    """Must validate UUIDs and skip random strings."""
    assert utils.is_valid_uuid(uuid) is result
