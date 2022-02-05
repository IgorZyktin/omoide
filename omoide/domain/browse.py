# -*- coding: utf-8 -*-
"""Preview related interfaces and objects.
"""
from pydantic import BaseModel

from omoide.domain.common import AccessStatus, Location, Item

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
    items: list[Item]
