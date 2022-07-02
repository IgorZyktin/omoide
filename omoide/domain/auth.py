# -*- coding: utf-8 -*-
"""User related interfaces and objects.
"""
from datetime import datetime
from typing import Optional, Mapping

from pydantic import BaseModel

from omoide.domain import utils

__all__ = [
    'User',
]


class User(BaseModel):
    """User model."""
    uuid: str
    login: str
    password: str
    name: str
    root_item: Optional[str]
    visibility: Optional[str]
    language: Optional[str]
    last_seen: Optional[datetime]

    def cannot_create_items(self) -> bool:
        """Return True if user is not allowed to create items."""
        return self.is_anon()

    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.uuid == ''

    def is_not_anon(self) -> bool:
        """Return True if user is registered one."""
        return not self.is_anon()

    @classmethod
    def from_map(cls, mapping: Mapping) -> 'User':
        """Convert from arbitrary format to model."""
        return cls(
            uuid=utils.as_str(mapping, 'uuid'),
            login=mapping['login'],
            password=mapping['password'],
            name=mapping['name'],
            root_item=utils.as_str(mapping, 'root_item'),
        )

    @classmethod
    def new_anon(cls) -> 'User':
        """Return new anon user."""
        return cls(
            uuid='',
            login='',
            password='',
            name='anon',
            root_item=None,
            visibility=None,
            language=None,
            last_seen=None,
        )
