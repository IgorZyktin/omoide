"""Web level API models."""

import base64
import math
from typing import Self
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

from omoide import const
from omoide import utils

MAX_MEDIA_SIZE = 52_428_800
MAX_MEDIA_SIZE_HR = utils.human_readable_size(MAX_MEDIA_SIZE)

SUPPORTED_EXTENSION = frozenset(
    (
        'jpg',
        'jpeg',
        'png',
        'webp',
    )
)

MAX_ITEM_FIELD_LENGTH = 256
MAX_TAGS = 100
MAX_PERMISSIONS = 100


class ItemInput(BaseModel):
    """Input info for item creation."""

    uuid: UUID | None = None
    parent_uuid: UUID | None = None
    owner_uuid: UUID | None = None
    name: str = Field('', max_length=MAX_ITEM_FIELD_LENGTH)
    number: int | None = None
    is_collection: bool = False
    tags: list[str] = Field([], max_length=MAX_TAGS)
    permissions: list[UUID] = Field([], max_length=MAX_PERMISSIONS)

    @model_validator(mode='after')
    def check_tags(self) -> 'ItemInput':
        """Raise if tag is too big."""
        for tag in self.tags:
            if len(tag) > MAX_ITEM_FIELD_LENGTH:
                msg = (
                    f'Tag is too long ({len(tag)} symbols), '
                    f'max allowed length is {MAX_ITEM_FIELD_LENGTH} symbols'
                )
                raise ValueError(msg)
        return self

    @model_validator(mode='after')
    def ensure_collection_has_name(self) -> 'ItemInput':
        """Raise if got nameless collection."""
        if self.is_collection and not self.name:
            msg = 'Collection must have a name'
            raise ValueError(msg)
        return self


class ItemUpdateInput(BaseModel):
    """Input info for item update."""

    is_collection: bool = False


class ItemRenameInput(BaseModel):
    """Input info for item rename."""

    name: str = Field('', max_length=MAX_ITEM_FIELD_LENGTH)


class MediaInput(BaseModel):
    """Input info for media creation."""

    content: str
    ext: str = Field(..., min_length=1)

    @model_validator(mode='after')
    def check_extension(self) -> Self:
        """Raise if we do not support this extension."""
        if self.ext.lower() not in SUPPORTED_EXTENSION:
            msg = (
                'Unsupported extension, '
                f'must be one of {sorted(SUPPORTED_EXTENSION)}'
            )
            raise ValueError(msg)
        return self

    @model_validator(mode='after')
    def check_size(self) -> Self:
        """Raise if content is too big."""
        if self.expected_binary_size > MAX_MEDIA_SIZE:
            msg = (
                'Sent content is too big, '
                f'maximum allowed size is {MAX_MEDIA_SIZE_HR}'
            )
            raise ValueError(msg)
        return self

    @property
    def expected_binary_size(self) -> int:
        """Return approximate content size after decoding."""
        return int(math.ceil(len(self.content) / 4) * 3)

    @property
    def binary_content(self) -> bytes:
        """Convert from base64 into bytes."""
        sep = self.content.index(',')
        body = self.content[sep + 1 :]
        return base64.decodebytes(body.encode('utf-8'))


class PermissionsInput(BaseModel):
    """Input info for new item permissions."""

    permissions: set[UUID]
    apply_to_parents: bool = False
    apply_to_children: bool = True
    apply_to_children_as: const.ApplyAs = const.ApplyAs.DELTA
