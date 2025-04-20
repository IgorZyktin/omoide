"""Remote operations."""

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
import enum
from typing import Any
from typing import Literal
from uuid import UUID

import python_utilz as pu

from omoide import const

DUMMY_UUID = UUID('00000000-0000-0000-0000-000000000000')


class OperationStatus(enum.StrEnum):
    """Possible statuses for operation."""

    CREATED = 'created'
    PROCESSING = 'processing'
    DONE = 'done'
    FAILED = 'failed'

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<{self.name.lower()}>'


@dataclass
class BaseOperation:
    """Base class."""

    requested_by: UUID
    id: int = -1
    name: str = 'base_serial_operation'
    status: OperationStatus = OperationStatus.CREATED
    extras: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=pu.now)
    updated_at: datetime = field(default_factory=pu.now)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    log: str | None = None
    payload: bytes = b''

    @classmethod
    def from_extras(
        cls,
        extras: dict[str, Any],
        **kwargs: Any,
    ) -> 'BaseOperation':
        """Create from database record."""
        requested_by = UUID(extras['requested_by'])
        return cls(requested_by=requested_by, extras=extras, **kwargs)

    def dump_extras(self) -> dict[str, Any]:
        """Convert extras to JSON."""
        extras: dict[str, Any] = {'requested_by': str(self.requested_by)}
        extras.update(self.extras)
        return extras

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<{type(self).__name__} id={self.id} {self.name!r} {self.extras}>'

    @property
    def duration(self) -> float:
        """Get execution duration."""
        if self.started_at is None:
            seconds = (self.updated_at - self.created_at).total_seconds()
        elif self.ended_at is None:
            seconds = (self.started_at - self.created_at).total_seconds()
        else:
            seconds = (self.ended_at - self.created_at).total_seconds()
        return seconds

    @property
    def hr_duration(self) -> str:
        """Return human-readable duration."""
        if (seconds := self.duration) > 1:
            duration = pu.human_readable_time(seconds)
        else:
            duration = f'{seconds:0.3f} sec.'
        return duration

    def add_to_log(self, text: str) -> None:
        """Store additional text."""
        if self.log is None:
            self.log = text
        else:
            self.log += f'\n{text}'

    def mark_done(self) -> None:
        """Alter state to `done`."""
        now = pu.now()
        self.updated_at = now
        self.ended_at = now
        self.status = OperationStatus.DONE

    def mark_updated(self) -> None:
        """Update, but do not finish yet."""
        now = pu.now()
        self.updated_at = now
        self.ended_at = now

    def mark_failed(self, worker_name: str, exc: Exception) -> str:
        """Alter state to `failed`."""
        now = pu.now()
        self.updated_at = now
        self.ended_at = now
        self.status = OperationStatus.FAILED
        error = pu.exc_to_str(exc)
        self.add_to_log(f'Worker {worker_name}: {error}')
        return error


@dataclass
class BaseSerialOperation(BaseOperation):
    """Base class."""

    worker_name: str | None = None


@dataclass
class RebuildKnownTagsForAnonOp(BaseSerialOperation):
    """Request for tags rebuilding."""

    name: str = 'rebuild_known_tags_for_anon'


@dataclass
class RebuildKnownTagsForUserOp(BaseSerialOperation):
    """Request for tags rebuilding."""

    name: str = 'rebuild_known_tags_for_user'
    user_uuid: UUID = DUMMY_UUID

    @classmethod
    def from_extras(
        cls,
        extras: dict[str, Any],
        **kwargs: Any,
    ) -> 'BaseOperation':
        """Create from database record."""
        requested_by = UUID(extras['requested_by'])
        user_uuid = UUID(extras['user_uuid'])
        return cls(requested_by=requested_by, user_uuid=user_uuid, extras=extras, **kwargs)

    def dump_extras(self) -> dict[str, Any]:
        """Convert extras to JSON."""
        extras = super().dump_extras()
        extras['user_uuid'] = str(self.user_uuid)
        return extras


@dataclass
class RebuildKnownTagsForAllOp(BaseSerialOperation):
    """Request for tags rebuilding."""


@dataclass
class RebuildComputedTagsForItemOp(BaseSerialOperation):
    """Request for tags rebuilding."""

    name: str = 'rebuild_computed_tags_for_item'
    item_uuid: UUID = DUMMY_UUID

    @classmethod
    def from_extras(
        cls,
        extras: dict[str, Any],
        **kwargs: Any,
    ) -> 'BaseOperation':
        """Create from database record."""
        requested_by = UUID(extras['requested_by'])
        item_uuid = UUID(extras['item_uuid'])
        return cls(requested_by=requested_by, item_uuid=item_uuid, extras=extras, **kwargs)

    def dump_extras(self) -> dict[str, Any]:
        """Convert extras to JSON."""
        extras = super().dump_extras()
        extras['item_uuid'] = str(self.item_uuid)
        return extras


@dataclass
class RebuildPermissionsForItemOp(BaseSerialOperation):
    """Request for permissions rebuilding."""

    name: str = 'rebuild_permissions_for_item'
    item_uuid: UUID = DUMMY_UUID
    added: set[int] = field(default_factory=set)
    deleted: set[int] = field(default_factory=set)
    original: set[int] = field(default_factory=set)
    apply_to_parents: bool = False
    apply_to_children: bool = False
    apply_to_children_as: str = const.ApplyAs.DELTA

    @classmethod
    def from_extras(
        cls,
        extras: dict[str, Any],
        **kwargs: Any,
    ) -> 'BaseOperation':
        """Create from database record."""
        kwargs.update(
            {
                'requested_by': UUID(extras['requested_by']),
                'item_uuid': UUID(extras['item_uuid']),
                'added': set(extras['added']),
                'deleted': set(extras['deleted']),
                'original': set(extras['original']),
                'apply_to_parents': extras['apply_to_parents'],
                'apply_to_children': extras['apply_to_children'],
                'apply_to_children_as': extras['apply_to_children_as'],
            }
        )
        return cls(**kwargs)

    def dump_extras(self) -> dict[str, Any]:
        """Convert extras to JSON."""
        extras = super().dump_extras()
        extras.update(
            {
                'item_uuid': str(self.item_uuid),
                'added': list(self.added),
                'deleted': list(self.deleted),
                'original': list(self.original),
                'apply_to_parents': self.apply_to_parents,
                'apply_to_children': self.apply_to_children,
                'apply_to_children_as': self.apply_to_children_as,
            }
        )
        return extras


@dataclass
class IntroduceItemOp(BaseSerialOperation):
    """Operation for item introduction (adding into the system)."""

    name: str = 'introduce_item'
    item_uuid: UUID = DUMMY_UUID

    @classmethod
    def from_extras(
        cls,
        extras: dict[str, Any],
        **kwargs: Any,
    ) -> 'BaseOperation':
        """Create from database record."""
        kwargs.update(
            {
                'requested_by': UUID(extras['requested_by']),
                'item_uuid': UUID(extras['item_uuid']),
            }
        )
        return cls(**kwargs)

    def dump_extras(self) -> dict[str, Any]:
        """Convert extras to JSON."""
        extras = super().dump_extras()
        extras['item_uuid'] = str(self.item_uuid)
        return extras


@dataclass
class BaseParallelOperation(BaseOperation):
    """Base class."""

    processed_by: set[str] = field(default_factory=set)

    @classmethod
    def from_extras(
        cls,
        extras: dict[str, Any],
        **kwargs: Any,
    ) -> 'BaseOperation':
        """Create from database record."""
        requested_by = UUID(extras['requested_by'])
        return cls(requested_by=requested_by, extras=extras, **kwargs)

    def dump_extras(self) -> dict[str, Any]:
        """Convert extras to JSON."""
        extras: dict[str, Any] = {'requested_by': str(self.requested_by)}
        extras.update(self.extras)
        return extras


@dataclass
class SoftDeleteMediaOp(BaseParallelOperation):
    """Soft media deletion."""

    item_uuid: UUID = DUMMY_UUID
    media_type: Literal['content', 'preview', 'thumbnail', ''] = ''
    name: str = 'soft_delete_media'

    @classmethod
    def from_extras(
        cls,
        extras: dict[str, Any],
        **kwargs: Any,
    ) -> 'BaseOperation':
        """Create from database record."""
        kwargs.update(
            {
                'requested_by': UUID(extras['requested_by']),
                'item_uuid': UUID(extras['item_uuid']),
                'media_type': extras['media_type'],
                'extras': extras,
            }
        )
        return cls(**kwargs)

    def dump_extras(self) -> dict[str, Any]:
        """Convert extras to JSON."""
        extras = super().dump_extras()
        extras.update(
            {
                'item_uuid': str(self.item_uuid),
                'media_type': self.media_type,
            }
        )
        return extras


@dataclass
class HardDeleteMediaOp(SoftDeleteMediaOp):
    """Hard media deletion."""

    name: str = 'hard_delete_media'


@dataclass
class DownloadMediaOp(SoftDeleteMediaOp):
    """Save media to the storage."""

    name: str = 'download_media'
