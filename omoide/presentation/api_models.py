# -*- coding: utf-8 -*-
"""Input and output models for the API.
"""
from typing import Optional
from uuid import UUID

import pydantic


class OnlyUUID(pydantic.BaseModel):
    """Simple model, that describes only UUID of the object."""
    uuid: UUID


class PatchOperation(pydantic.BaseModel):
    """Single operation in PATCH request."""
    op: str
    path: str
    value: str | bool | None = None


class ItemByName(pydantic.BaseModel):
    """Simple model, that helps find item by its name."""
    name: str


class CreateItemIn(pydantic.BaseModel):
    """Input info for item creation."""
    uuid: Optional[UUID] = None
    parent_uuid: Optional[UUID] = None
    name: str
    is_collection: bool
    tags: list[str]
    permissions: list[UUID]

    @pydantic.field_validator('name')
    @classmethod
    def name_must_have_adequate_length(cls, v):
        """Check."""
        name_limit = 255
        if len(v) > name_limit:
            raise ValueError(
                f'Name is too long (maximums {name_limit} characters)'
            )
        return v

    @pydantic.field_validator('tags')
    @classmethod
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

    @pydantic.field_validator('permissions')
    @classmethod
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

    @pydantic.model_validator(mode='before')
    @classmethod
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


class CreateUserIn(pydantic.BaseModel):
    """Input info for user creation."""
    uuid: Optional[UUID] = None
    root_item: Optional[UUID] = None
    login: str
    password: str
    name: Optional[str] = None


class NewTagsIn(pydantic.BaseModel):
    """Input info for new tags."""
    tags: list[str]
    # TODO - add validation


class NewPermissionsIn(pydantic.BaseModel):
    """Input info for new permissions."""
    apply_to_parents: bool
    apply_to_children: bool
    override: bool
    permissions_before: list[UUID]
    permissions_after: list[UUID]
