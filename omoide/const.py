"""Global constants."""

from datetime import UTC
from datetime import datetime
import enum
from typing import Literal
from typing import TypeAlias
from uuid import UUID

VERSION = '0.3.10'

FRONTEND_VERSION = 20

DUMMY_UUID = UUID('00000000-0000-0000-0000-000000000000')
DUMMY_TIME = datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=UTC)

CONTENT: Literal['content'] = 'content'
PREVIEW: Literal['preview'] = 'preview'
THUMBNAIL: Literal['thumbnail'] = 'thumbnail'
MEDIA_TYPE: TypeAlias = Literal['content', 'preview', 'thumbnail']
MEDIA_TYPES: list[MEDIA_TYPE] = [CONTENT, PREVIEW, THUMBNAIL]

AUTH_COMPLEXITY = 4  # minimal

ANON: Literal['anon'] = 'anon'

ASC: Literal['asc'] = 'asc'
DESC: Literal['desc'] = 'desc'
RANDOM: Literal['random'] = 'random'
ORDER_TYPE: TypeAlias = Literal['asc', 'desc', 'random']

DEF_COLLECTIONS = False
DEF_DIRECT = False
DEF_ORDER = RANDOM

PAGES_IN_ALBUM_AT_ONCE = 10

# for path generation i.e.
# /home/storage/<owner uuid>/00/109a6c44-c75f-4c71-aada-b22f15aa9a02.jpg
STORAGE_PREFIX_SIZE = 2

# Environment variables
ENV_FOLDER = 'OMOIDE__FOLDER'
ENV_DB_URL_ADMIN = 'OMOIDE__DB_URL_ADMIN'


class ApplyAs(enum.StrEnum):
    """How to apply changes."""

    DELTA = 'delta'
    COPY = 'copy'


class AllSerialOperations(enum.StrEnum):
    """All possible serial operations."""

    REBUILD_ITEM_TAGS = 'rebuild_item_tags'
    REBUILD_ITEM_PERMISSIONS = 'rebuild_item_permissions'
    REBUILD_KNOWN_TAGS_ALL = 'rebuild_known_tags_all'
    REBUILD_KNOWN_TAGS_USER = 'rebuild_known_tags_user'
    REBUILD_KNOWN_TAGS_ANON = 'rebuild_known_tags_anon'
