"""Global constants."""
from datetime import datetime
from datetime import timezone
from typing import Literal
from typing import TypeAlias
from uuid import UUID

VERSION = '0.3.8'

FRONTEND_VERSION = 7

DUMMY_UUID = UUID('00000000-0000-0000-0000-000000000000')
DUMMY_TIME = datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)

CONTENT: Literal['content'] = 'content'
PREVIEW: Literal['preview'] = 'preview'
THUMBNAIL: Literal['thumbnail'] = 'thumbnail'
MEDIA_TYPE: TypeAlias = Literal['content', 'preview', 'thumbnail']
MEDIA_TYPES: list[MEDIA_TYPE] = [CONTENT, PREVIEW, THUMBNAIL]

AUTH_COMPLEXITY = 4  # minimal

ANON: Literal['anon'] = 'anon'

DB_BATCH_SIZE = 200

ASC: Literal['asc'] = 'asc'
DESC: Literal['desc'] = 'desc'
RANDOM: Literal['random'] = 'random'
ORDER_TYPE: TypeAlias = Literal['asc', 'desc', 'random']
