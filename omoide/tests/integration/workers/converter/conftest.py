"""Fixtures shared by converter worker tests."""

import pytest


@pytest.fixture
def user_and_item(make_item):
    """Insert one user + one item; return ``(user_uuid, item_uuid)``."""
    _item_id, item_uuid, owner_uuid = make_item()
    return owner_uuid, item_uuid
