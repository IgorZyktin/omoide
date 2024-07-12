"""Raw models that come from user.
"""
import base64

import pydantic

from omoide import const


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
