"""Logic models."""
import abc
import enum
from collections import UserString
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import SecretStr

from omoide import const
from omoide import utils


@dataclass
class ModelMixin(abc.ABC):
    """Mixin that adds functionality similar to pydantic."""

    def model_dump(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Convert model to dictionary."""
        dump = asdict(self)

        if not exclude:
            return dump

        return {
            key: value
            for key, value in dump.items()
            if key in exclude
        }


# TODO - Use this in model instead of pydantic one
class SecretStrCustom(UserString):
    """String class that adds functionality similar to pydantic."""

    def get_secret_value(self) -> str:
        """Get the secret value."""
        return self.data

    def __str__(self) -> str:
        """Return textual representation."""
        return '***'

    def __repr__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'{name}(***)'


class Role(enum.Enum):
    """User role."""
    # TODO - change to StrEnum in Python 3.11
    anon = enum.auto()
    user = enum.auto()
    admin = enum.auto()


class User(BaseModel):
    """User model."""
    uuid: UUID
    name: str
    login: SecretStr
    password: SecretStr
    role: Role
    root_item: UUID | None = None  # TODO - remove this field

    def __str__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'<{name} {self.uuid} {self.name}>'

    @property
    def is_admin(self) -> bool:
        """Return True if user is an administrator."""
        return self.role is Role.admin

    @property
    def is_not_admin(self) -> bool:
        """Return True if user is not an administrator."""
        return self.role is not Role.admin

    @property
    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.role is Role.anon

    @property
    def is_not_anon(self) -> bool:
        """Return True if user is registered one."""
        return self.role is not Role.anon

    @classmethod
    def new_anon(cls) -> 'User':  # TODO - replace with Self
        """Return new anon user."""
        return cls(
            uuid=const.DUMMY_UUID,
            login=SecretStr(''),
            password=SecretStr(''),
            name=const.ANON,
            role=Role.anon,
            root_item=None,  # TODO - remove this field
        )


class Metainfo(BaseModel):
    """Metainfo for item."""
    created_at: datetime = const.DUMMY_TIME
    updated_at: datetime = const.DUMMY_TIME
    deleted_at: datetime | None = None
    user_time: datetime | None = None

    content_type: str | None = None

    author: str | None = None
    author_url: str | None = None
    saved_from_url: str | None = None
    description: str | None = None

    extras: dict[str, Any] = Field(default_factory=dict)

    content_size: int | None = None
    preview_size: int | None = None
    thumbnail_size: int | None = None

    content_width: int | None = None
    content_height: int | None = None
    preview_width: int | None = None
    preview_height: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None


@dataclass
class SpaceUsage(ModelMixin):
    """Total size of user data for specific user."""
    uuid: UUID
    content_size: int
    preview_size: int
    thumbnail_size: int

    def __str__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return (
            f'<{name}, uuid={self.uuid}, '
            f'content={self.content_size_hr}, '
            f'preview={self.preview_size_hr}, '
            f'thumbnail={self.thumbnail_size_hr}>'
        )

    def __repr__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return (
            f'{name}(uuid={self.uuid!r}, '
            f'content_size={self.content_size}, '
            f'preview_size={self.preview_size}, '
            f'thumbnail_size={self.thumbnail_size})'
        )

    @classmethod
    def empty(cls, uuid: UUID) -> 'SpaceUsage':  # TODO - replace with Self
        """Return result with zero bytes used."""
        return cls(
            uuid=uuid,
            content_size=0,
            preview_size=0,
            thumbnail_size=0,
        )

    @property
    def content_size_hr(self) -> str:
        """Return human-readable value."""
        return utils.human_readable_size(self.content_size)

    @property
    def preview_size_hr(self) -> str:
        """Return human-readable value."""
        return utils.human_readable_size(self.preview_size)

    @property
    def thumbnail_size_hr(self) -> str:
        """Return human-readable value."""
        return utils.human_readable_size(self.thumbnail_size)
