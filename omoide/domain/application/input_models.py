"""Raw models that come from user.
"""
import base64
from typing import Literal

import pydantic

from omoide.domain.core import core_constants


class InEXIF(pydantic.BaseModel):
    """Input info for EXIF creation."""
    exif: dict[str, str | float | int | bool | None | list | dict]


class InMedia(pydantic.BaseModel):
    """Input info for media creation."""
    content: str
    target_folder: Literal['content', 'preview', 'thumbnail']
    ext: str

    @pydantic.field_validator('target_folder')
    @classmethod
    def check_media_type(cls, v):
        """Check."""
        if v not in core_constants.MEDIA_TYPES:
            msg = f'Incorrect media type: {v}'
            raise ValueError(msg)
        return v

    @property
    def binary_content(self) -> bytes:
        """Convert from base64 into bytes."""
        sep = self.content.index(',')
        body = self.raw_content[sep + 1:]
        return base64.decodebytes(body.encode('utf-8'))
