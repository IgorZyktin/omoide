"""All possible serial operations."""

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
import enum
from functools import cached_property
from typing import Any
from uuid import UUID

from omoide import const
from omoide import exceptions
from omoide import utils

_ALL_SERIAL_OPERATIONS: dict[str, type['SerialOperation']] = {}


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
class SerialOperation:
    """Base class for all serial operations."""

    id: int = -1
    name: str = ''
    worker_name: str | None = None
    status: OperationStatus = OperationStatus.CREATED
    extras: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utils.now)
    updated_at: datetime = field(default_factory=utils.now)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    log: str | None = None

    goal: str = ''

    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        """Store descendant."""
        _ALL_SERIAL_OPERATIONS[cls.name] = cls
        super().__init_subclass__(*args, **kwargs)

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<{self.id}, {self.name!r}>'

    @staticmethod
    def from_name(name: str, **kwargs: Any) -> 'SerialOperation':
        """Create specific instance type."""
        operation_type = _ALL_SERIAL_OPERATIONS.get(name)

        if operation_type is None:
            raise exceptions.UnknownSerialOperationError(name=name)

        return operation_type(**kwargs)

    @property
    def duration(self) -> float:
        """Get execution duration."""
        if self.started_at is None or self.ended_at is None:
            return 0.0
        return (self.ended_at - self.started_at).total_seconds()

    def add_to_log(self, text: str) -> None:
        """Store additional text."""
        if self.log is None:
            self.log = text
        else:
            self.log += f'\n{text}'


@dataclass
class DummySO(SerialOperation):
    """Operation for testing purposes."""

    name: str = 'dummy'
    goal: str = 'to test things'


@dataclass
class RebuildKnownTagsAnonSO(SerialOperation):
    """Rebuild known tags for anon."""

    name: str = 'rebuild_known_tags_anon'
    goal: str = 'rebuild known tags for anon'


@dataclass
class RebuildKnownTagsUserSO(SerialOperation):
    """Rebuild known tags registered anon."""

    name: str = 'rebuild_known_tags_user'
    goal: str = 'rebuild known tags for {user}'

    @cached_property
    def user_uuid(self) -> UUID:
        """Extract from extras."""
        return UUID(self.extras['user_uuid'])


@dataclass
class RebuildKnownTagsAllSO(SerialOperation):
    """Rebuild known tags for registered user."""

    name: str = 'rebuild_known_tags_all'
    goal: str = 'rebuild known tags for all users'


@dataclass
class UpdatePermissionsSO(SerialOperation):
    """Update permission in item and all dependant objects."""

    name: str = 'update_permissions'
    goal: str = 'update permissions for item'

    @cached_property
    def item_uuid(self) -> UUID:
        """Extract from extras."""
        return UUID(self.extras['item_uuid'])

    @cached_property
    def added(self) -> set[UUID]:
        """Extract from extras."""
        return {UUID(x) for x in self.extras['added']}

    @cached_property
    def deleted(self) -> set[UUID]:
        """Extract from extras."""
        return {UUID(x) for x in self.extras['deleted']}

    @cached_property
    def original(self) -> set[UUID]:
        """Extract from extras."""
        return {UUID(x) for x in self.extras['original']}

    @cached_property
    def apply_to_parents(self) -> bool:
        """Extract from extras."""
        return bool(self.extras['apply_to_parents'])

    @cached_property
    def apply_to_children(self) -> bool:
        """Extract from extras."""
        return bool(self.extras['apply_to_children'])

    @cached_property
    def apply_to_children_as(self) -> const.ApplyAs:
        """Extract from extras."""
        return const.ApplyAs(self.extras['apply_to_children_as'])


@dataclass
class UpdateTagsSO(SerialOperation):
    """Update tags for given item and maybe all children."""

    name: str = 'update_tags'
    goal: str = 'update tags for item'

    @cached_property
    def item_uuid(self) -> UUID:
        """Extract from extras."""
        return UUID(self.extras['item_uuid'])

    @cached_property
    def apply_to_children(self) -> bool:
        """Extract from extras."""
        return bool(self.extras['apply_to_children'])


@dataclass
class DropVisibilitySO(SerialOperation):
    """After item deletion, it must be wiped out from known tags."""

    name: str = 'drop_visibility'
    goal: str = 'hide item from known tags'

    @cached_property
    def item_uuid(self) -> UUID:
        """Extract from extras."""
        return UUID(self.extras['item_uuid'])
