# -*- coding: utf-8 -*-
"""Input and output models for the API.
"""
from datetime import datetime
from typing import Literal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import root_validator
from pydantic import validator


class OnlyUUID(BaseModel):
    """Simple model, that describes only UUID of the object."""
    uuid: UUID


class PatchOperation(BaseModel):
    """Single operation in PATCH request."""
    op: str
    path: str
    value: str | None


class CreateItemIn(BaseModel):
    """Input info for item creation."""
    uuid: Optional[UUID]
    parent_uuid: Optional[UUID]
    name: str
    is_collection: bool
    tags: list[str]
    permissions: list[UUID]

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
            if len(str(permission)) > permissions_name_limit:
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


class CreateItemsIn(CreateItemIn):
    """Input info for bulk item creation."""
    total: int


class CreateUserIn(BaseModel):
    """Input info for user creation."""
    uuid: Optional[UUID]
    root_item: Optional[UUID]
    login: str
    password: str
    name: Optional[str]


class CreateMediaIn(BaseModel):
    """Input info for media creation."""
    content: str
    target_folder: Literal['content', 'preview', 'thumbnail']
    ext: str


class EXIFIn(BaseModel):
    """Input info for EXIF creation."""
    exif: dict[str, str | float | int | bool | None | list | dict]


class NewTagsIn(BaseModel):
    """Input info for new tags."""
    tags: list[str]
    # TODO - add validation


class NewPermissionsIn(BaseModel):
    """Input info for new permissions."""
    apply_to_parents: bool
    apply_to_children: bool
    override: bool
    permissions_before: list[UUID]
    permissions_after: list[UUID]


class MetainfoIn(BaseModel):
    """Input info for metainfo creation."""
    user_time: Optional[datetime]

    media_type: Optional[str]

    author: Optional[str]
    author_url: Optional[str]
    saved_from_url: Optional[str]
    description: Optional[str]

    extras: dict

    content_size: Optional[int] = None
    preview_size: Optional[int] = None
    thumbnail_size: Optional[int] = None

    content_width: Optional[int] = None
    content_height: Optional[int] = None
    preview_width: Optional[int] = None
    preview_height: Optional[int] = None
    thumbnail_width: Optional[int] = None
    thumbnail_height: Optional[int] = None
