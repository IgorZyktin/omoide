"""Web level API models."""
import base64
import math

from pydantic import BaseModel
from pydantic import model_validator

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


class MediaInput(BaseModel):
    """Input info for media creation."""
    content: str
    ext: str

    @model_validator(mode='after')
    def check_extension(self) -> 'MediaInput':
        """Raise if we do not support this extension."""
        if self.ext.lower() not in SUPPORTED_EXTENSION:
            msg = (
                'Unsupported extension, '
                f'must be one of {sorted(SUPPORTED_EXTENSION)}'
            )
            raise ValueError(msg)
        return self

    @model_validator(mode='after')
    def check_size(self) -> 'MediaInput':
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
        body = self.content[sep + 1:]
        return base64.decodebytes(body.encode('utf-8'))
