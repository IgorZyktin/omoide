# -*- coding: utf-8 -*-
"""Preview related interfaces and objects.
"""
from pydantic import BaseModel

from omoide.domain import common

__all__ = [
    'Result',
]


class Result(BaseModel):
    """Result of a search request."""
    access: common.AccessStatus
    location: common.Location
    page: int
    total_items: int
    total_pages: int
    items: list[common.Item]
