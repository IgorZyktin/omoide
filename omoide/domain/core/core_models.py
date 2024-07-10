"""Business-logic models.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from omoide.domain import common

# FIXME - temporary import
AccessStatus = common.AccessStatus


@dataclass
class GuessResult:
    """Variants that can possibly match with user guess."""
    tag: str
    counter: int


@dataclass
class Media:
    """Transient content fot the item."""
    id: int
    created_at: datetime
    processed_at: datetime | None
    error: str
    owner_uuid: UUID
    item_uuid: UUID
    media_type: str
    content: bytes
    ext: str
