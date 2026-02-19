"""Domain-level models."""

import abc
from collections.abc import Collection
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
import enum
from typing import Any
from typing import Literal
from typing import NamedTuple
from typing import Self
from uuid import UUID

import python_utilz as pu

from omoide import const


class OmoideModel(abc.ABC):
    """Base class for all Omoide models."""

    _ignore_changes: frozenset[str] = frozenset()
    _changes: set[str] = set()  # noqa: RUF012

    def __post_init__(self) -> None:
        """Clear all newly set attributes."""
        self._changes.clear()

    def __setattr__(self, attr: str, value: Any) -> None:
        """Set attribute and track changes."""
        if attr != '_changes':
            _changes = self.__dict__.setdefault('_changes', set())
            _changes.add(attr)
        super().__setattr__(attr, value)

    def what_changed(self) -> frozenset[str]:
        """Return changed attributes."""
        return frozenset(self._changes)

    def get_changes(self, ignore_changes: Collection[str] = ()) -> dict[str, Any]:
        """Return changed attributes."""
        ignore_changes = ignore_changes or self._ignore_changes
        return {key: getattr(self, key) for key in self._changes if key not in ignore_changes}

    def mark_changed(self, key: str) -> None:
        """Store the fact that this attribute has changed."""
        self._changes.add(key)

    def reset_changes(self) -> None:
        """Clear all changed attributes."""
        self._changes.clear()

    def model_dump(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Convert model to dictionary."""
        exclude = exclude or set()
        return {
            key: value
            for key, value in asdict(self).items()  # type: ignore[call-overload]
            if key not in exclude and not key.startswith('_')
        }

    @classmethod
    @abc.abstractmethod
    def from_obj(
        cls,
        obj: Any,
        extra_keys: Collection[str] = (),
        extras: dict[str, Any] | None = None,
    ) -> Self:
        """Create instance from arbitrary object."""


class Role(enum.IntEnum):
    """User role."""

    USER = 0
    ANON = 1
    ADMIN = 2


@dataclass
class User(OmoideModel):
    """User model."""

    id: int
    uuid: UUID
    name: str
    login: str
    role: Role
    is_public: bool
    registered_at: datetime
    last_login: datetime | None
    timezone: str | None
    lang: str | None

    extras: dict[str, Any]  # ephemeral attribute

    _ignore_changes: frozenset[str] = frozenset(('id', 'uuid'))

    def __eq__(self, other: object) -> bool:
        """Return True if other has the same UUID."""
        return bool(self.uuid == getattr(other, 'uuid', None))

    def __hash__(self) -> int:
        """Return hash of UUID."""
        return hash(self.uuid)

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<User id={self.id} {self.uuid} {self.name}>'

    @property
    def is_admin(self) -> bool:
        """Return True if user is an administrator."""
        return self.role == Role.ADMIN

    @property
    def is_not_admin(self) -> bool:
        """Return True if user is not an administrator."""
        return self.role != Role.ADMIN

    @property
    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.role == Role.ANON

    @property
    def is_not_anon(self) -> bool:
        """Return True if user is registered one."""
        return self.role != Role.ANON

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
            registered_at=pu.now(),
            last_login=None,
            timezone=None,
            lang=None,
            extras={},
        )

    @classmethod
    def from_obj(
        cls,
        obj: Any,
        extra_keys: Collection[str] = (),
        extras: dict[str, Any] | None = None,
    ) -> Self:
        """Create instance from arbitrary object."""
        if extras is not None:
            _extras = extras
        elif extra_keys:
            _extras = {key: getattr(obj, key) for key in extra_keys}
        else:
            _extras = {}

        return cls(
            id=obj.id,
            uuid=obj.uuid,
            name=obj.name,
            login=obj.login,
            role=obj.role,
            is_public=obj.is_public,
            registered_at=obj.registered_at,
            last_login=obj.last_login,
            timezone=None,  # TODO - actually use it
            lang=None,  # TODO - actually use it
            extras=_extras,
        )


class Status(enum.IntEnum):
    """Item status."""

    AVAILABLE = 0
    CREATED = 1
    PROCESSING = 2
    DELETED = 3
    ERROR = 4


@dataclass
class Item(OmoideModel):
    """Standard item."""

    id: int
    uuid: UUID
    parent_uuid: UUID | None
    owner_uuid: UUID
    parent_id: int | None
    owner_id: int
    number: int
    name: str
    is_collection: bool
    content_ext: str | None
    preview_ext: str | None
    thumbnail_ext: str | None
    status: Status
    tags: set[str]
    permissions: set[int]

    extras: dict[str, Any]  # ephemeral attribute

    _ignore_changes: frozenset[str] = frozenset(('id', 'uuid'))

    def __eq__(self, other: object) -> bool:
        """Return True if other has the same UUID."""
        return bool(self.uuid == getattr(other, 'uuid', None))

    def __hash__(self) -> int:
        """Return hash of UUID."""
        return hash(self.uuid)

    def __str__(self) -> str:
        """Return textual representation."""
        if self.name:
            return f'<Item id={self.id} {self.uuid} {self.name}>'
        return f'<Item id={self.id} {self.uuid}>'

    def has_incomplete_media(self) -> bool:
        """Return True if not media types are present for this item."""
        return None in (self.content_ext, self.preview_ext, self.thumbnail_ext)

    def get_computed_tags(self, parent_name: str, parent_tags: set[str]) -> set[str]:
        """Return computed tags.

        Resulting collection is not visible for users and includes
        technical information.
        """
        computed_tags: set[str] = {tag.casefold() for tag in self.tags}

        if _parent_name := parent_name.strip():
            computed_tags.add(_parent_name.casefold())

        if self.is_collection and (_name := self.name.strip()):
            computed_tags.add(_name.casefold())

        computed_tags.update(parent_tags)

        if self.parent_uuid is not None:
            computed_tags.add(str(self.parent_uuid))

        computed_tags.add(str(self.uuid).casefold())

        return computed_tags

    @classmethod
    def from_obj(
        cls,
        obj: Any,
        extra_keys: Collection[str] = (),
        extras: dict[str, Any] | None = None,
    ) -> Self:
        """Create instance from arbitrary object."""
        if extras is not None:
            _extras = extras
        elif extra_keys:
            _extras = {key: getattr(obj, key) for key in extra_keys}
        else:
            _extras = {}

        return cls(
            id=obj.id,
            uuid=obj.uuid,
            parent_id=obj.parent_id,
            parent_uuid=obj.parent_uuid,
            owner_id=obj.owner_id,
            owner_uuid=obj.owner_uuid,
            name=obj.name,
            number=obj.number,
            is_collection=obj.is_collection,
            content_ext=obj.content_ext,
            preview_ext=obj.preview_ext,
            thumbnail_ext=obj.thumbnail_ext,
            status=Status(obj.status),
            tags=set(obj.tags),
            permissions=set(obj.permissions),
            extras=_extras,
        )


@dataclass
class Metainfo(OmoideModel):
    """Metainfo for item."""

    item_id: int

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

    _ignore_changes: frozenset[str] = frozenset(('item_id',))

    @classmethod
    def from_obj(
        cls,
        obj: Any,
        extra_keys: Collection[str] = (),
        extras: dict[str, Any] | None = None,
    ) -> Self:
        """Create instance from arbitrary object."""
        _ = extra_keys
        _ = extras
        return cls(
            item_id=obj.item_id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            deleted_at=obj.deleted_at,
            user_time=obj.user_time,
            content_type=obj.content_type,
            content_size=obj.content_size,
            preview_size=obj.preview_size,
            thumbnail_size=obj.thumbnail_size,
            content_width=obj.content_width,
            content_height=obj.content_height,
            preview_width=obj.preview_width,
            preview_height=obj.preview_height,
            thumbnail_width=obj.thumbnail_width,
            thumbnail_height=obj.thumbnail_height,
        )


@dataclass
class Media(OmoideModel):
    """Transient content fot the item."""

    id: int
    created_at: datetime
    processed_at: datetime | None
    error: str | None
    owner_id: int
    item_id: int
    media_type: str
    content: bytes
    ext: str

    _ignore_changes: frozenset[str] = frozenset(('id',))

    @classmethod
    def from_obj(
        cls,
        obj: Any,
        extra_keys: Collection[str] = (),
        extras: dict[str, Any] | None = None,
    ) -> Self:
        """Create instance from arbitrary object."""
        _ = extra_keys
        _ = extras
        return cls(
            id=obj.id,
            created_at=obj.created_at,
            processed_at=obj.processed_at,
            error=obj.error,
            owner_id=obj.owner_id,
            item_id=obj.item_id,
            media_type=obj.media_type,
            content=obj.content,
            ext=obj.ext,
        )


@dataclass
class SpaceUsage:
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
        return pu.human_readable_size(self.content_size)

    @property
    def preview_size_hr(self) -> str:
        """Return human-readable value."""
        return pu.human_readable_size(self.preview_size)

    @property
    def thumbnail_size_hr(self) -> str:
        """Return human-readable value."""
        return pu.human_readable_size(self.thumbnail_size)


@dataclass
class DiskUsage:
    """Total disk usage of a specific user."""

    content_bytes: int
    preview_bytes: int
    thumbnail_bytes: int

    @property
    def content_hr(self) -> str:
        """Return human-readable value."""
        return pu.human_readable_size(self.content_bytes)

    @property
    def preview_hr(self) -> str:
        """Return human-readable value."""
        return pu.human_readable_size(self.preview_bytes)

    @property
    def thumbnail_hr(self) -> str:
        """Return human-readable value."""
        return pu.human_readable_size(self.thumbnail_bytes)


@dataclass
class ResourceUsage:
    """Total resource usage for specific user."""

    user_uuid: UUID
    total_items: int
    total_collections: int
    disk_usage: DiskUsage


class ParentTags(NamedTuple):
    """DTO for parent computed tags."""

    parent: Item
    computed_tags: set[str]


@dataclass
class Plan:
    """Search definition according to user request."""

    query: str
    tags_include: set[str]
    tags_exclude: set[str]
    order: Literal['asc', 'desc', 'random']
    collections: bool
    direct: bool
    last_seen: int | None
    limit: int


@dataclass
class DuplicateExample:
    """One duplicated inheritance line."""

    item: Item
    parents: list[Item]


@dataclass
class Duplicate:
    """DTO that describes group of items with same image signature."""

    signature: str
    examples: list[DuplicateExample]


@dataclass
class Features:
    """Special parameters for upload."""

    extract_exif: bool | None = None
    last_modified: datetime | None = None


@dataclass
class NewFile:
    """Raw file uploaded by user."""

    content: bytes = b''
    content_type: str = ''
    filename: str = ''
    ext: str = ''
    features: Features = field(default_factory=Features)


@dataclass
class Exif:
    """Exchangeable Image File Format data."""

    exif: dict[str, Any]


@dataclass
class InputMedia:
    """What we received from user."""

    id: int
    item_id: int
    created_at: datetime
    filename: str
    content_type: str
    extras: dict
    error: str | None
    content: bytes
