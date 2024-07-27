"""Web level API models."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import NonNegativeInt
from pydantic import model_validator

from omoide import utils

MAXIMUM_EXTRAS_SIZE = 1024 * 1024 * 5  # MiB

_BASE_EXAMPLE = {
    'user_time': '2022-02-16 19:51:14.321331+00:00',
    'content_type': 'image/jpeg',
    'extras': {
        'original_file_name': 'IMG_6607.jpg'
    },
    'content_width': 2104,
    'content_height': 1480,
    'preview_width': 1456,
    'preview_height': 1024,
    'thumbnail_width': 548,
    'thumbnail_height': 384,
}


class MetainfoInput(BaseModel):
    """Metainfo for item."""
    user_time: datetime | None = None
    content_type: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)

    content_width: NonNegativeInt | None = None
    content_height: NonNegativeInt | None = None

    preview_width: NonNegativeInt | None = None
    preview_height: NonNegativeInt | None = None

    thumbnail_width: NonNegativeInt | None = None
    thumbnail_height: NonNegativeInt | None = None

    model_config = {
        'json_schema_extra': {
            'examples': [_BASE_EXAMPLE]
        }
    }

    @model_validator(mode='after')
    def ensure_extras_are_not_too_big(self) -> 'MetainfoInput':  # TODO - Self
        """Raise if given string is too big."""
        size = utils.get_size(self.extras)
        if size > MAXIMUM_EXTRAS_SIZE:
            hr_size = utils.human_readable_size(size)
            hr_limit = utils.human_readable_size(MAXIMUM_EXTRAS_SIZE)
            msg = (
                f'Given item extras are too big (got {hr_size}), '
                f'allowed maximum is {hr_limit}'
            )
            raise ValueError(msg)
        return self


class MetainfoOutput(BaseModel):
    """Metainfo for item."""
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    user_time: str | None = None

    content_type: str | None = None

    author: str | None = None
    author_url: str | None = None
    saved_from_url: str | None = None
    description: str | None = None

    extras: dict[str, Any] = Field(default_factory=dict)

    content_size: int | None = None
    preview_size: int | None = None
    thumbnail_size: int | None = None

    content_width: int | None = None
    content_height: int | None = None
    preview_width: int | None = None
    preview_height: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'created_at': '2022-02-16 19:51:14.321331+00:00',
                    'updated_at': '2022-02-16 19:51:14.321331+00:00',
                    'deleted_at': None,
                    **_BASE_EXAMPLE,
                }
            ]
        }
    }
