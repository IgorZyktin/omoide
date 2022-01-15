# -*- coding: utf-8 -*-
"""Search related interfaces and objects.
"""
from pydantic import BaseModel

__all__ = [
    'SimpleItem',
    'Result',
    'Query',
]


class SimpleItem(BaseModel):
    """Primitive version of an item."""
    owner_uuid: str | None
    uuid: str
    is_collection: bool
    name: str
    ext: str | None

    @property
    def location(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{self.uuid[:2]}/{self.uuid}.{self.ext}'


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
