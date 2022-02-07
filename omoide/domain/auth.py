# -*- coding: utf-8 -*-
"""User related interfaces and objects.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, UUID4

__all__ = [
    'User',
]


class User(BaseModel):
    """User model."""
    uuid: Optional[UUID4]
    login: str
    password: str
    name: str
    visibility: Optional[str]
    language: Optional[str]
    last_seen: Optional[datetime]

    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.uuid is None
