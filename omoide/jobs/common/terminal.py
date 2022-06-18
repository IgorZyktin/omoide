# -*- coding: utf-8 -*-
"""Terminal and CLI related stuff.
"""
__all__ = [
    'TERMINAL_WIDTH',
    'MAXLEN_UUID',
    'MAXLEN_OWNER_NAME',
    'MAXLEN_FILE_NAME',
    'MAXLEN_STATUS',
    'MAXLEN_MEDIA_TYPE',
    'MAXLEN_MEDIA_SIZE',
    'get_rest_of_the_terminal_width',
]

# use wide terminal for job operations
TERMINAL_WIDTH = 200

# formatting settings
MAXLEN_UUID = 38
MAXLEN_OWNER_NAME = 16
MAXLEN_FILE_NAME = 32
MAXLEN_STATUS = 8
MAXLEN_MEDIA_TYPE = 11
MAXLEN_MEDIA_SIZE = 14


def get_rest_of_the_terminal_width(*columns: int, max_width: int) -> int:
    """Calculate all what's left after column filling."""
    total = sum(columns) + len(columns) + 1  # include also table lines
    rest = max_width - total

    if rest <= 0:
        raise ValueError('Got no space left to output anything')

    return rest
