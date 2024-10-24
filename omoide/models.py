"""Logic models."""

import abc
import enum
from collections import UserString
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import Generic
from typing import NamedTuple
from typing import Self
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from omoide import const
from omoide import exceptions
from omoide import utils


@dataclass
class ModelMixin:
    """Mixin that adds functionality similar to pydantic."""

    def model_dump(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Convert model to dictionary."""
        dump = asdict(self)

        if not exclude:
            return dump

        return {
            key: value for key, value in dump.items() if key not in exclude
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


class Role(enum.IntEnum):
    """User role."""

    USER = 0
    ANON = 1
    ADMIN = 2


@dataclass
class User(ModelMixin):
    """User model."""

    id: int
    uuid: UUID
    name: str
    login: str
    role: Role
    is_public: bool

    def __eq__(self, other: object) -> bool:
        """Return True if other has the same UUID."""
        return bool(self.id == getattr(other, 'id', None))

    def __hash__(self) -> int:
        """Return hash of UUID."""
        return hash(self.id)

    def __str__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'<{name} {self.id} {self.uuid} {self.name}>'

    @property
    def is_admin(self) -> bool:
        """Return True if user is an administrator."""
        return self.role is Role.ADMIN

    @property
    def is_not_admin(self) -> bool:
        """Return True if user is not an administrator."""
        return self.role is not Role.ADMIN

    @property
    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.role is Role.ANON

    @property
    def is_not_anon(self) -> bool:
        """Return True if user is registered one."""
        return self.role is not Role.ANON

    @classmethod
    def new_anon(cls) -> Self:
        """Return new anon user."""
        return cls(
            id=-1,
            uuid=const.DUMMY_UUID,
            name=const.ANON,
            login='',
            role=Role.ANON,
            is_public=False,
        )


@dataclass
class AccessStatus(ModelMixin):
    """Status of an access and existence check."""

    exists: bool
    is_public: bool
    is_permitted: bool
    is_owner: bool

    @property
    def does_not_exist(self) -> bool:
        """Return True if item does not exist."""
        return not self.exists

    @property
    def is_given(self) -> bool:
        """Return True if user can access this item."""
        return any(
            [
                self.is_public,
                self.is_owner,
                self.is_permitted,
            ]
        )

    @property
    def is_not_given(self) -> bool:
        """Return True if user cannot access this item."""
        return not self.is_given

    @property
    def is_not_owner(self) -> bool:
        """Return True if user is not owner of the item."""
        return not self.is_owner

    @classmethod
    def not_found(cls) -> 'AccessStatus':
        """Item does not exist."""
        return cls(
            exists=False,
            is_public=False,
            is_permitted=False,
            is_owner=False,
        )


class Status(enum.IntEnum):
    """Item status."""

    AVAILABLE = 0
    CREATED = 1
    PROCESSING = 2
    DELETED = 3
    ERROR = 4


@dataclass
class Item(ModelMixin):
    """Standard item."""

    id: int
    uuid: UUID
    parent_uuid: UUID | None
    owner_uuid: UUID
    number: int
    name: str
    is_collection: bool
    content_ext: str | None
    preview_ext: str | None
    thumbnail_ext: str | None
    status: Status = Status.AVAILABLE  # TODO - make it mandatory
    tags: list[str] = field(default_factory=list)
    permissions: list[UUID] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        """Return True if other has the same UUID."""
        return bool(self.uuid == getattr(other, 'uuid', None))

    def __hash__(self) -> int:
        """Return hash of UUID."""
        return hash(self.uuid)

    def __str__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        if self.name:
            return f'<{name} {self.uuid} {self.name}>'
        return f'<{name} {self.uuid}>'

    def get_computed_tags(self, parent_tags: set[str]) -> set[str]:
        """Return computed tags.

        Resulting collection is not visible for users and includes
        technical information.
        """
        computed_tags: set[str] = {tag.casefold() for tag in self.tags}

        computed_tags.add(str(self.uuid).casefold())

        if self.name.strip():
            computed_tags.add(self.name.strip().casefold())

        computed_tags.update(parent_tags)

        if self.parent_uuid is not None:
            computed_tags.add(str(self.parent_uuid))

        return computed_tags


class MetainfoOld(BaseModel):
    """Metainfo for item."""

    created_at: datetime = const.DUMMY_TIME
    updated_at: datetime = const.DUMMY_TIME
    deleted_at: datetime | None = None
    user_time: datetime | None = None

    content_type: str | None = None
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
class Metainfo(ModelMixin):
    """Metainfo for item."""

    item_uuid: UUID

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    user_time: datetime | None

    content_type: str | None
    extras: dict[str, Any]

    content_size: int | None
    preview_size: int | None
    thumbnail_size: int | None

    content_width: int | None
    content_height: int | None
    preview_width: int | None
    preview_height: int | None
    thumbnail_width: int | None
    thumbnail_height: int | None


@dataclass
class Media(ModelMixin):
    """Transient content fot the item."""

    id: int
    created_at: datetime
    processed_at: datetime | None
    error: str | None
    owner_uuid: UUID
    item_uuid: UUID
    media_type: str
    content: bytes
    ext: str


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


@dataclass
class DiskUsage(ModelMixin):
    """Total disk usage of a specific user."""

    content_bytes: int
    preview_bytes: int
    thumbnail_bytes: int

    @property
    def content_hr(self) -> str:
        """Return human-readable value."""
        return utils.human_readable_size(self.content_bytes)

    @property
    def preview_hr(self) -> str:
        """Return human-readable value."""
        return utils.human_readable_size(self.preview_bytes)

    @property
    def thumbnail_hr(self) -> str:
        """Return human-readable value."""
        return utils.human_readable_size(self.thumbnail_bytes)


@dataclass
class ResourceUsage(ModelMixin):
    """Total resource usage for specific user."""

    user_uuid: UUID
    total_items: int
    total_collections: int
    disk_usage: DiskUsage


class ParentTags(NamedTuple):
    """DTO for parent computed tags."""

    parent: Item
    computed_tags: set[str]


class OperationStatus(enum.StrEnum):
    """Possible statuses for operation."""

    CREATED = 'created'
    PROCESSING = 'processing'
    DONE = 'done'
    FAILED = 'failed'

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<{self.name.lower()}>'


ALL_SERIAL_OPERATIONS: dict[str, type['SerialOperation']] = {}

ConfigT = TypeVar('ConfigT')
MediatorT = TypeVar('MediatorT')


@dataclass
class SerialOperation(Generic[ConfigT, MediatorT], abc.ABC):
    """Base class for all serial operations."""

    id: int
    worker_name: str
    status: OperationStatus
    extras: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    log: str | None
    name: str = 'operation'
    goal: str = 'unknown'

    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        """Store descendant."""
        ALL_SERIAL_OPERATIONS[cls.name] = cls
        super().__init_subclass__(*args, **kwargs)

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<{self.id}, {self.name!r}>'

    @staticmethod
    def from_name(**kwargs: Any) -> 'SerialOperation':
        """Create specific instance type."""
        name = kwargs['name']
        class_ = ALL_SERIAL_OPERATIONS.get(name)

        if class_ is None:
            raise exceptions.UnknownSerialOperationError(name=name)

        return class_(**kwargs)

    @staticmethod
    def get_all_possible_operations() -> set[str]:
        """Return set of names for all descendants."""
        return set(ALL_SERIAL_OPERATIONS.keys())

    @abc.abstractmethod
    def execute(self, config: ConfigT, mediator: MediatorT) -> None:
        """Perform workload."""

    @property
    def duration(self) -> float:
        """Get execution duration."""
        if self.started_at is None or self.ended_at is None:
            return 0.0
        return (self.ended_at - self.started_at).total_seconds()
