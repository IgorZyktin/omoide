"""Global constants."""
from typing import Literal
from uuid import UUID

DUMMY_UUID = UUID('00000000-0000-0000-0000-000000000000')

CONTENT: Literal['content'] = 'content'
PREVIEW: Literal['preview'] = 'preview'
THUMBNAIL: Literal['thumbnail'] = 'thumbnail'
MEDIA_TYPE = Literal['content', 'preview', 'thumbnail']
MEDIA_TYPES: list[MEDIA_TYPE] = [CONTENT, PREVIEW, THUMBNAIL]

AUTH_COMPLEXITY = 4  # minimal
