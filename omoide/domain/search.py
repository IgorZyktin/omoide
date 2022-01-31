# -*- coding: utf-8 -*-
"""Search related interfaces and objects.
"""
from pydantic import BaseModel

from omoide.domain.common import SimpleItem

__all__ = [
    'Result',
]


class Result(BaseModel):
    """Result of a search request."""
    is_random: bool
    page: int
    total_items: int
    total_pages: int
    items: list[SimpleItem]
