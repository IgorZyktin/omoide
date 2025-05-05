"""Remote operations."""

from dataclasses import dataclass
from datetime import datetime
import enum
from typing import Any

import python_utilz as pu


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
class Operation:
    """ParallelOperation."""

    id: int
    name: str
    status: OperationStatus
    extras: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    log: str | None
    payload: bytes
    processed_by: set[str]

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
            duration = f'{seconds: 0.3f} sec.'
        return duration
