# -*- coding: utf-8 -*-
"""Common utils.
"""
import datetime
import re
from uuid import UUID


def now() -> datetime.datetime:
    """Return current moment in time with timezone."""
    return datetime.datetime.now(tz=datetime.timezone.utc)


def get_bucket(uuid: UUID | str, length: int = 2) -> str:
    """Get bucket name from uuid.

    >>> get_bucket('92b0fa01-72a3-4300-9bb7-5a440da37f93')
    '92'
    """
    if isinstance(uuid, str):
        return str(UUID(uuid))[:length]
    return str(uuid)[:length]


UUID_TEMPLATE = re.compile(
    '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
)


def is_valid_uuid(uuid: UUID | str) -> bool:
    """Return True if given object can be considered as UUID."""
    if isinstance(uuid, UUID):
        return True
    return UUID_TEMPLATE.match(uuid) is not None
