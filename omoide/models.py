"""Domain-level models."""
import enum
from collections.abc import Collection
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import NamedTuple
from typing import Self
from uuid import UUID

from omoide import const
from omoide import utils


@dataclass
class ModelMixin:
    """Mixin that adds functionality similar to pydantic."""

    def model_dump(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Convert model to dictionary."""
        dump = asdict(self)

        if not exclude:
            return dump

        return {key: value for key, value in dump.items() if key not in exclude}


@dataclass
class ChangesMixin:
    """Mixin that tracks changes in its attributes."""
    _changes: set[str] = field(default_factory=set)
    _ignore_changes: tuple[str] = ('id',)

    def __post_init__(self) -> None:
        """Clear all newly set attributes."""
        self.reset_changes()

    def __setattr__(self, attr: str, value: Any) -> None:
        """Set attribute and track changes."""
        if attr != '_changes':
            self._changes.add(attr)
        super().__setattr__(attr, value)

    def what_changed(self, ignore_fields: Collection[str] = ()) -> dict[str, Any]:
        """Return changed attributes."""
        ignore = ignore_fields or self._ignore_changes
        return {key: getattr(self, key) for key in self._changes if key not in ignore}

    def mark_changed(self, key: str) -> None:
        """Store the fact that this attribute has changed."""
        self._changes.add(key)

    def reset_changes(self) -> None:
        """Clear all changed attributes."""
        self._changes.clear()


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
    registered_at: datetime
    last_login: datetime | None

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

    @property
    def timezone(self) -> None:
        """Return timezone for this user."""
        # TODO - add timezone to users
        return None

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
            registered_at=utils.now(),
            last_login=None,
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
    tags: set[str] = field(default_factory=set)
    permissions: set[UUID] = field(default_factory=set)

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


@dataclass(kw_only=True)
class Metainfo(ModelMixin, ChangesMixin):
    """Metainfo for item."""

    item_uuid: UUID

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    user_time: datetime | None

    content_type: str | None

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
    def empty(cls, uuid: UUID) -> Self:
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
