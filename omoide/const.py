"""Global constants."""
from datetime import datetime
from datetime import timezone
from typing import Literal
from typing import TypeAlias
from uuid import UUID

VERSION = '0.3.9'

FRONTEND_VERSION = 9

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

PAGES_IN_ALBUM_AT_ONCE = 10

# for path generation i.e.
# /home/storage/<owner uuid>/00/109a6c44-c75f-4c71-aada-b22f15aa9a02.jpg
STORAGE_PREFIX_SIZE = 2
