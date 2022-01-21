# -*- coding: utf-8 -*-
"""Preview related interfaces and objects.
"""
from pydantic import BaseModel

from omoide.domain.common import AccessStatus, Location, SimpleItem

__all__ = [
    'AccessStatus',
    'Result',
]


class Result(BaseModel):
    """Result of a search request."""
    access: AccessStatus
    location: Location
    page: int
    total_items: int
    total_pages: int
    items: list[SimpleItem]


class Query(BaseModel):
    """User search query."""
    tags_include: list[str]
    tags_exclude: list[str]
    page: int
    items_per_page: int = 10
