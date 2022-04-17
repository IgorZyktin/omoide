# -*- coding: utf-8 -*-
"""CRUD related interfaces and objects.
"""
from pydantic import BaseModel

__all__ = [
    'CreateItemPayload',
]


class CreateItemPayload(BaseModel):
    """Payload for item creation."""
    parent_uuid: str
    item_name: str
    is_collection: bool
    tags: list[str]
    permissions: list[str]
