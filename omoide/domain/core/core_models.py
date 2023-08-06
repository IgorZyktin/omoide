"""Business-logic models.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from omoide.domain import auth

# FIXME - temporary import
User = auth.User


@dataclass(eq=True)
class EXIF:
    """EXIF information embedded in media."""
    item_uuid: UUID
    exif: dict[str, str | float | int | bool | None | list | dict]


@dataclass
class GuessResult:
    """Variants that can possibly match with user guess."""
    tag: str
    counter: int


@dataclass
class Media:
    """Transient content fot the item."""
    id: int
    owner_uuid: UUID
    item_uuid: UUID
    content: bytes
    ext: str
    target_folder: Literal['content', 'preview', 'thumbnail']
    replication: dict[str, dict]
    error: str
    attempts: int
    created_at: datetime
    processed_at: datetime | None = None
