# -*- coding: utf-8 -*-
"""ByUser related interfaces and objects.
"""
from pydantic import BaseModel

from omoide.domain import common

__all__ = [
    'Result',
]


class Result(BaseModel):
    """Complete output of ByUser request."""
    page: int
    total_items: int
    total_pages: int
    items: list[common.Item]
