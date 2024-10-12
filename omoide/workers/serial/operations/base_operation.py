"""Base class for all serial operations."""

import abc
from dataclasses import dataclass
from datetime import datetime
import enum
from typing import Any

from omoide import custom_logging

LOG = custom_logging.get_logger(__name__)

ALL_OPERATIONS: dict[str, type['Operation']] = {}


# TODO - change to StrEnum in Python 3.11
class Status(enum.Enum):
    """Possible statuses for operation."""

    CREATED = enum.auto()
    PROCESSING = enum.auto()
    DONE = enum.auto()
    FAILED = enum.auto()

    def __str__(self) -> str:
        """Return textual representation."""
        return self.name.lower()

    @staticmethod
    def from_string(name: str) -> 'Status':
        """Convert to class."""
        match name:
            case 'created':
                result = Status.CREATED
            case 'processing':
                result = Status.PROCESSING
            case 'done':
                result = Status.DONE
            case 'failed':
                result = Status.FAILED
            case _:
                msg = f'Unknown status {name!r}'
                raise RuntimeError(msg)

        return result


@dataclass
class Operation(abc.ABC):
    """Base class for all serial operations."""

    id: int
    status: Status
    expected: int
    affected: int
    extras: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    log: str | None
    name: str = 'operation'

    def __init_subclass__(cls, *args, **kwargs):
        """Store descendant."""
        super().__init_subclass__(*args, **kwargs)
        ALL_OPERATIONS[cls.name] = cls

    @staticmethod
    def from_raw(**kwargs) -> 'Operation':
        """Create specific instance type."""
        name = kwargs['name']
        class_ = ALL_OPERATIONS.get(name)
        if class_ is None:
            msg = f'There is no operation of type {name!r}'
            raise RuntimeError(msg)

        return class_(**kwargs)

    @abc.abstractmethod
    async def execute(self) -> bool:
        """Perform workload."""
