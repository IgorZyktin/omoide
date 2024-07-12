"""Web level API models."""
import base64

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

MAX_LENGTH_FOR_MEDIA_TYPE = 64
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
    # TODO - check input size somehow
    content: str
    media_type: str = Field(..., max_length=MAX_LENGTH_FOR_MEDIA_TYPE)
    ext: str

    @model_validator(mode='after')
    def check_extension(self) -> 'MediaInput':
        """Raise if we do not support this extension."""
        # TODO - manage extensions as a constant somehow
        if self.ext.lower() not in SUPPORTED_EXTENSION:
            msg = (
                'Unsupported extension, '
                f'must be one of {sorted(SUPPORTED_EXTENSION)}'
            )
            raise ValueError(msg)
        return self

    def get_binary_content(self) -> bytes:
        """Convert from base64 into bytes."""
        sep = self.content.index(',')
        body = self.content[sep + 1:]
        return base64.decodebytes(body.encode('utf-8'))
