"""Global constants."""
from uuid import UUID

DUMMY_UUID = UUID('00000000-0000-0000-0000-000000000000')

CONTENT = 'content'
PREVIEW = 'preview'
THUMBNAIL = 'thumbnail'
MEDIA_TYPES = [CONTENT, PREVIEW, THUMBNAIL]

AUTH_COMPLEXITY = 4  # minimal
