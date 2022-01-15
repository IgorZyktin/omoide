# -*- coding: utf-8 -*-
"""User related interfaces and objects.
"""
from datetime import datetime

from pydantic import BaseModel, UUID4

__all__ = [
    'User',
]


class User(BaseModel):
    """User model."""
    uuid: UUID4 | None
    login: str
    password: str
    name: str
    visibility: str | None
    language: str | None
    last_seen: datetime | None

    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.uuid is None
