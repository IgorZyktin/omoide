# -*- coding: utf-8 -*-
"""CRUD related interfaces and objects.
"""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel

__all__ = [
    'CreateItemPayload',
    'RawMedia',
]


class CreateItemPayload(BaseModel):
    """Payload for item creation."""
    uuid: Optional[UUID]
    parent_uuid: str
    item_name: str
    is_collection: bool
    tags: list[str]
    permissions: list[str]


class RawMedia(BaseModel):
    """Payload for raw media creation."""
    uuid: UUID
    created_at: datetime
    processed_at: Optional[datetime]
    status: Literal['init', 'work', 'done', 'fail']
    filename: str
    content: bytes
    features: list[str]
