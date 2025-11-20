"""Global limitation constants."""

import python_utilz as pu

# Search query
DEF_QUERY = ''
MIN_QUERY = 2
MAX_QUERY = 512

MIN_LIMIT = 1
MAX_LIMIT = 200
DEF_LIMIT = 30

MIN_BROWSE = 1
MAX_BROWSE = 200
DEF_BROWSE = 25

DEF_LAST_SEEN = None

MIN_AUTOCOMPLETE = 2
AUTOCOMPLETE_LIMIT = 10

# Items
MAX_ITEM_FIELD_LENGTH = 256
MAX_TAGS = 100
MAX_PERMISSIONS = 100

# Media
MAX_MEDIA_SIZE = 1024 * 1024 * 50  # 50 MiB
MAX_MEDIA_SIZE_HR = pu.human_readable_size(MAX_MEDIA_SIZE)

SUPPORTED_EXTENSION = frozenset(
    (
        'jpg',
        'jpeg',
        'png',
        'webp',
    )
)
