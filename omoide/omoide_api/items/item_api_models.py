"""Web level API models."""
import base64
import math
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
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


class ItemOutput(BaseModel):
    """Output form of an item."""
    uuid: UUID
    parent_uuid: UUID | None
    owner_uuid: UUID
    number: int
    name: str
    is_collection: bool
    content_ext: str | None
    preview_ext: str | None
    thumbnail_ext: str | None
    tags: list[str] = []
    permissions: list[UUID] = []

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'uuid': 'f2528be0-73bc-4808-bda6-3d54e7b80950',
                    'parent_uuid': '2ef3086c-79a7-4a84-9f17-fa602a3467dc',
                    'owner_uuid': 'c044fc6d-394d-4dd3-a0bf-41df10cab01a',
                    'number': 68695,
                    'name': 'Something',
                    'is_collection': True,
                    'content_ext': 'jpg',
                    'preview_ext': 'jpg',
                    'thumbnail_ext': 'jpg',
                    'tags': ['tag1', 'tag2'],
                    'permissions': ['c044fc6d-394d-4dd3-a0bf-41df10cab01a'],
                }
            ]
        }
    }


class MediaInput(BaseModel):
    """Input info for media creation."""
    content: str
    ext: str = Field(..., min_length=1)

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
