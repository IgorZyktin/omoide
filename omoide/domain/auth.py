"""User related interfaces and objects."""
import enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

__all__ = [
    'Role',
    'User',
]


class Role(enum.StrEnum):
    """User role."""
    anon = enum.auto()
    user = enum.auto()
    admin = enum.auto()


class User(BaseModel):
    """User model."""
    uuid: Optional[UUID] = None
    login: str
    password: str
    name: str
    root_item: Optional[UUID] = None
    role: Role

    @property
    def is_admin(self) -> bool:
        """Return True if user is an administrator."""
        return self.role is Role.admin

    @property
    def is_registered(self) -> bool:
        """Return True if user is registered."""
        return self.uuid is not None

    @property
    def is_not_registered(self) -> bool:
        """Return True if user is anon."""
        return self.uuid is None

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
            role=Role.anon,
        )
