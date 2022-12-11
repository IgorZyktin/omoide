# -*- coding: utf-8 -*-
"""User related interfaces and objects.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

__all__ = [
    'User',
]


class User(BaseModel):
    """User model."""
    uuid: Optional[UUID]
    login: str
    password: str
    name: str
    root_item: Optional[UUID]

    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.uuid is None

    def is_not_anon(self) -> bool:
        """Return True if user is registered one."""
        return not self.is_anon()

    @classmethod
    def new_anon(cls) -> 'User':
        """Return new anon user."""
        return cls(
            uuid=None,
            login='',
            password='',
            name='anon',
            root_item=None,
        )
