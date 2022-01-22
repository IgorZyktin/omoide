# -*- coding: utf-8 -*-
"""Search related interfaces and objects.
"""
from pydantic import BaseModel

from omoide.domain.common import SimpleItem

__all__ = [
    'Result',
    'Query',
]


class Result(BaseModel):
    """Result of a search request."""
    is_random: bool
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

    def __bool__(self) -> bool:
        """Return True if query has tags to search."""
        return any((
            self.tags_include,
            self.tags_exclude,
        ))

    @property
    def offset(self) -> int:
        """Return offset from start of the result block."""
        return self.items_per_page * (self.page - 1)
