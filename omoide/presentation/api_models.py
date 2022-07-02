# -*- coding: utf-8 -*-
"""Input and output models for the API.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, validator, root_validator


class OnlyUUID(BaseModel):
    """Simple model, that describes only UUID of the object."""
    uuid: UUID


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
        name_limit = 255
        if len(v) > name_limit:
            raise ValueError(
                f'Name is too long (maximums {name_limit} characters)'
            )
        return v

    @validator('tags')
    def tags_must_be_adequate(cls, v):
        """Check."""
        tags_limit = 255
        if len(v) > tags_limit:
            raise ValueError(
                f'Too many tags (maximum {tags_limit} tags)'
            )

        tag_name_limit = 255
        for tag in v:
            if len(tag) > tag_name_limit:
                raise ValueError(
                    f'Tag is too long (maximum {tag_name_limit} characters)'
                )

        return v

    @validator('permissions')
    def permissions_be_adequate(cls, v):
        """Check."""
        permissions_limit = 100
        if len(v) > permissions_limit:
            raise ValueError(
                f'Too many permissions (maximum is {permissions_limit})'
            )

        permissions_name_limit = 255
        for permission in v:
            if len(permission) > permissions_name_limit:
                raise ValueError(
                    'Permission name is too long '
                    f'(maximum {permissions_name_limit} characters)'
                )

        return v

    @root_validator
    def ensure_collection_has_name(cls, values: dict):
        """Check."""
        name = values.get('name')
        is_collection = values.get('is_collection')

        if is_collection and not name:
            raise ValueError('Collection has to have a name')

        return values


class UpdateItemIn(CreateItemIn):
    """Input info for item update."""
    uuid: UUID
    content_ext: Optional[str]
    preview_ext: Optional[str]
    thumbnail_ext: Optional[str]
