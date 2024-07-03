"""User related interfaces and objects."""
import enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from omoide import const

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
    uuid: UUID
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
    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.role is Role.anon

    @property
    def is_not_anon(self) -> bool:
        """Return True if user is registered one."""
        return self.role is not Role.anon

    @classmethod
    def new_anon(cls) -> 'User':
        """Return new anon user."""
        return cls(
            uuid=const.DUMMY_UUID,
            login='',
            password='',
            name='anon',
            root_item=None,
            role=Role.anon,
        )
