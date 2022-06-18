# -*- coding: utf-8 -*-
"""CRUD related interfaces and objects.
"""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, validator, root_validator

__all__ = [
    'CreateItemIn',
    'UpdateItemIn',
    'RawMedia',
]


class CreateItemIn(BaseModel):
    """Input info for item creation."""
    uuid: Optional[UUID]
    parent_uuid: Optional[UUID]
    name: str
    is_collection: bool
    tags: list[str]
    permissions: list[str]

    @validator('name')
    def name_must_have_adequate_length(cls, v):
        """Check."""
        if len(v) > 255:
            raise ValueError('Name is too long')
        return v

    @validator('tags')
    def tags_must_be_adequate(cls, v):
        """Check."""
        if len(v) > 255:
            raise ValueError('Too many tags')

        for tag in v:
            if len(tag) > 255:
                raise ValueError(f'Tag is too long {tag!r}')

        return v

    @validator('permissions')
    def permissions_be_adequate(cls, v):
        """Check."""
        if len(v) > 100:
            raise ValueError('Too many permissions')

        for permission in v:
            if len(permission) > 255:
                raise ValueError(f'Permission is too long {permission!r}')

        return v

    @root_validator
    def ensure_collection_has_name(cls, values: dict):
        """Check."""
        name = values.get('name')
        is_collection = values.get('is_collection')

        if is_collection and not name:
            raise ValueError('You have to specify name for collection')

        return values


class UpdateItemIn(CreateItemIn):
    """Input info for item update."""
    uuid: UUID
    content_ext: Optional[str]
    preview_ext: Optional[str]
    thumbnail_ext: Optional[str]


class RawMedia(BaseModel):
    """Payload for raw media creation."""
    uuid: UUID
    created_at: datetime
    processed_at: Optional[datetime]
    status: Literal['init', 'work', 'done', 'fail']
    filename: str
    content: bytes
    features: list[str]
    signature: str
