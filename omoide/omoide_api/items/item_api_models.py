"""Web level API models."""

import base64
from dataclasses import fields
from datetime import datetime
import math
from typing import Any
from typing import Self
from uuid import UUID

from fastapi import Request
from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

from omoide import const
from omoide import custom_logging
from omoide import limits
from omoide import models

LOG = custom_logging.get_logger(__name__)


class ItemUpdateInput(BaseModel):
    """Input info for item update."""

    is_collection: bool = False


class ItemRenameInput(BaseModel):
    """Input info for item rename."""

    name: str = Field('', max_length=limits.MAX_ITEM_FIELD_LENGTH)


class ItemUpdateTagsInput(BaseModel):
    """Input info for item tags update."""

    tags: set[str] = Field(set(), max_length=limits.MAX_TAGS)

    @model_validator(mode='after')
    def check_tags(self) -> Self:
        """Raise if tag is too big."""
        for tag in self.tags:
            if len(tag) > limits.MAX_ITEM_FIELD_LENGTH:
                msg = (
                    f'Tag is too long ({len(tag)} symbols), '
                    f'max allowed length is {limits.MAX_ITEM_FIELD_LENGTH} symbols'
                )
                raise ValueError(msg)
        return self


class MediaInput(BaseModel):
    """Input info for media creation."""

    content: str
    ext: str = Field(..., min_length=1)

    @model_validator(mode='after')
    def check_extension(self) -> Self:
        """Raise if we do not support this extension."""
        if self.ext.lower() not in limits.SUPPORTED_EXTENSION:
            msg = f'Unsupported extension, must be one of {sorted(limits.SUPPORTED_EXTENSION)}'
            raise ValueError(msg)
        return self

    @model_validator(mode='after')
    def check_size(self) -> Self:
        """Raise if content is too big."""
        if self.expected_binary_size > limits.MAX_MEDIA_SIZE:
            msg = f'Sent content is too big, maximum allowed size is {limits.MAX_MEDIA_SIZE_HR}'
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


def extract_features(request: Request) -> models.Features:
    """Extract features from headers."""
    headers = {key.lower(): value for key, value in request.headers.items()}
    params: dict[str, Any] = {}

    for field in fields(models.Features):
        suffix = field.name.replace('_', '-')
        name = f'x-feature-{suffix}'
        value = headers.get(name)

        if value is None:
            params[field.name] = None
        elif value.lower() == 'true':
            params[field.name] = True
        elif value.lower() == 'false':
            params[field.name] = False
        elif value.lower() == 'null':
            params[field.name] = None
        elif field.name == 'last_modified':
            try:
                params[field.name] = datetime.fromisoformat(value)
            except ValueError:
                LOG.exception('Incorrect format for `last_modified` header')
                params[field.name] = None
        else:
            params[field.name] = value

    return models.Features(**params)
