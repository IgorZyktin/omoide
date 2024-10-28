"""Information about the API itself."""

from omoide import const

__version__ = const.VERSION

DESCRIPTION = """
Backend of Omoide application.
"""

TAGS_METADATA = [
    {
        'name': 'Info',
        'description': 'Technical information about the API.',
    },
    {
        'name': 'Home',
        'description': 'Endpoint for the starting page.',
    },
    {
        'name': 'Search',
        'description': 'Operations with user search requests.',
    },
    {
        'name': 'Browse',
        'description': 'Requesting items in a tailored way.',
    },
    {
        'name': 'Users',
        'description': 'Operations with users.',
    },
    {
        'name': 'Items',
        'description': 'Operations with items.',
    },
    {
        'name': 'Metainfo',
        'description': 'Operations with item metainfo.',
    },
    {
        'name': 'EXIF',
        'description': 'Operations with item EXIF info.',
    },
    {
        'name': 'Actions',
        'description': 'Computationally heavy operations.',
    },
]
