# -*- coding: utf-8 -*-
"""CRUD related interfaces and objects.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

__all__ = [
    'CreateItemPayload',
]


class CreateItemPayload(BaseModel):
    """Payload for item creation."""
    uuid: Optional[UUID]
    parent_uuid: str
    item_name: str
    is_collection: bool
    tags: list[str]
    permissions: list[str]
