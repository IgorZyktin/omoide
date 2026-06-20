"""Models for parallel worker."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from functools import cached_property
from typing import Any


class CommandStatus(StrEnum):
    """Task status."""

    CREATED = 'created'
    ACTIVE = 'active'
    DONE = 'done'
    FAILED = 'failed'


@dataclass(frozen=True)
class ParallelCommand:
    """ParallelCommand."""

    id: int
    requested_by: int
    name: str
    status: CommandStatus
    extras: dict[str, Any]
    log: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime
    ended_at: datetime

    @cached_property
    def item_id(self) -> int:
        """Extract from extras."""
        item_id = self.extras.get('item_id')

        if item_id is None:
            msg = 'Missing item_id'
            raise KeyError(msg)

        return int(item_id)
