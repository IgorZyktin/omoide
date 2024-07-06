"""Raw models that come from user.
"""
import base64
from datetime import datetime

import pydantic

from omoide import const


class InEXIF(pydantic.BaseModel):
    """Input info for EXIF creation."""
    exif: dict[str, str | float | int | bool | None | list | dict]


class InMedia(pydantic.BaseModel):
    """Input info for media creation."""
    content: str
    media_type: str
    ext: str

    @pydantic.field_validator('media_type')
    @classmethod
    def check_media_type(cls, v):
        """Check."""
        if v not in const.MEDIA_TYPES:
            msg = (f'Incorrect media type: {v}, '
                   f'must be one of {const.MEDIA_TYPES}')
            raise ValueError(msg)
        return v

    def get_binary_content(self) -> bytes:
        """Convert from base64 into bytes."""
        sep = self.content.index(',')
        body = self.content[sep + 1:]
        return base64.decodebytes(body.encode('utf-8'))


class InMetainfo(pydantic.BaseModel):
    """Input info for metainfo creation."""
    user_time: datetime | None = None

    content_type: str | None = None

    author: str | None = None
    author_url: str | None = None
    saved_from_url: str | None = None
    description: str | None = None

    extras: dict | None = None

    content_size: int | None = None
    preview_size: int | None = None
    thumbnail_size: int | None = None

    content_width: int | None = None
    content_height: int | None = None
    preview_width: int | None = None
    preview_height: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None
