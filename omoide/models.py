"""Logic models."""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from omoide import const


class Role(enum.Enum):
    """User role."""
    # FEATURE - change to StrEnum in Python 3.11
    anon = enum.auto()
    user = enum.auto()
    admin = enum.auto()


class User(BaseModel):
    """User model."""
    uuid: UUID
    name: str
    login: str  # FEATURE - change to SecretStr
    password: str  # FEATURE - change to SecretStr
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


class Metainfo(BaseModel):
    """Metainfo for item."""
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    user_time: datetime | None = None

    content_type: str | None = None

    author: str | None = None
    author_url: str | None = None
    saved_from_url: str | None = None
    description: str | None = None

    extras: dict

    content_size: int | None = None
    preview_size: int | None = None
    thumbnail_size: int | None = None

    content_width: int | None = None
    content_height: int | None = None
    preview_width: int | None = None
    preview_height: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None


class SpaceUsage(BaseModel):
    """Total size of user data for specific user."""
    uuid: UUID
    content_size: int
    preview_size: int
    thumbnail_size: int

    @classmethod
    def empty(cls, uuid: UUID) -> 'SpaceUsage':
        """Return empty result."""
        return cls(
            uuid=uuid,
            content_size=0,
            preview_size=0,
            thumbnail_size=0,
        )
